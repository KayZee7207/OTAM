from typing import NamedTuple, Union, Literal
import html
import struct
import re
from .replays import Header, Replay

# Log Line Types
LogLine = Union[
  tuple[float, int, int, Literal["JOINED"], str],
  tuple[float, int, int, Literal["LEFT"], str],
  tuple[float, int, int, Literal["MSG"], str],
  tuple[float, int, int, Literal["PAUSE"], str],
  tuple[float, int, int, Literal["PING"], str],
  tuple[float, int, int, Literal["PING"], tuple[Literal["PING"], list[float]]],
  tuple[float, int, int, Literal["DRAW"], tuple[Literal["DRAW"], list[tuple[float, int, int, int, int]]]],
  tuple[float, int, int, Literal["SHARE"], str],
]

class Player(NamedTuple):
  index: int
  name: str
  spectator: int = 1
  id: str = None
  rank: int = None
  skill: str = None
  skilluncertainty: float = None
  countrycode: str = "NCC"
  allyteam: int = None
  side: str = None
  rgbcolor: tuple[float, float, float] = None

class Summary(NamedTuple):
  header: Header
  rawScript: str
  game: dict
  players: dict[int, Player]
  startTime: float
  logLines: list[LogLine]
  winningAllyTeams: list[int]

def decode(b: bytes):
  try: return b.decode()
  except: return b.decode("iso-8859-1")

def extract_share_event(data: bytes, players: dict[int, Player]):
  if len(data) < 9 or data[0] != 50:
    return None

  sender_index = int(data[3])
  message_length = int(data[1]) - 7
  if message_length <= 0:
    return None

  try:
    decoded = decode(data[7:7 + message_length]).strip()
  except Exception:
    return None

  if not decoded:
    return None

  match = re.match(
    r"msg:ui\.playersList\.chat\.give(?P<resource>Metal|Energy):amount=(?P<amount>[\d.,]+):name=(?P<target>.+)",
    decoded,
    flags=re.IGNORECASE,
  )
  if not match:
    return None

  resource = match.group("resource").lower()
  amount = match.group("amount").strip()
  target = match.group("target").strip()
  sender_name = players[sender_index].name if sender_index in players else f"Player {sender_index}"

  return 255, 255, f"{sender_name} shared {amount} {resource} to {target}"

def process_replay(replay: Replay) -> Summary:
  game = replay.setupScript['game']

  teams = {
    i: dict(
      allyteam=team["allyteam"],
      side=team["side"],
      rgbcolor=team["rgbcolor"],
    ) for i, team in enumerate(game.get("team", []))
  }

  players = {
    i: Player(
      index=i,
      id=player.get("accountid"),
      name=str(player["name"]),
      spectator=player.get("spectator"),
      rank=player.get("rank"),
      skill=player.get("skill"),
      skilluncertainty=player.get("skilluncertainty"),
      countrycode=player.get("countrycode", "NCC"),
      **(teams[player["team"]] if "team" in player and player["team"] in teams else {}),
    ) for i, player in enumerate(game.get('player', []))
  }

  startTime = 0
  playerCache = {} # a cache to sum up some consecutive actions
  logLines = []
  
  for gameTime, data in replay.chunks:
    if not data: continue
    action = int(data[0])
    
    # game start event
    if action == 4: startTime = gameTime
    
    # new spectator joined event
    if action == 75:
      player = int(data[3])
      spectator = int(data[4])
      team = int(data[5])
      name = decode(data[6:])
      if player not in players:
        players[player] = Player(
          index=player,
          name=str(name),
          spectator=spectator,
        )
      logLines.append((gameTime, player, None, "JOINED", "Player joined"))
      
    # player left
    if action == 39:
      player = int(data[1])
      if player in players:
          reason = {
            0: "Connection error",
            1: "Resigned" if not players[player].spectator else "Left",
            2: "Kicked",
          }.get(int(data[2]), "Unknown reason")
          logLines.append((gameTime, player, None, "LEFT", "Player left: " + reason))
          
    # chat message
    if action == 7:
      msgFrom = int(data[2])
      msgTo = int(data[3])
      msgStr = decode(data[4:-1])
      logLines.append((gameTime, msgFrom, msgTo, "MSG", msgStr))
      playerCache.pop(msgFrom, None)
      
    # game pause/unpause
    if action == 13:
      player_index = int(data[1])
      mode = int(data[2])
      player_name = players[player_index].name if player_index in players else "Unknown Player"
      if mode == 1:
        logLines.append((gameTime, 255, None, "PAUSE", player_name + " paused the game"))
      else:
        logLines.append((gameTime, 255, None, "PAUSE", player_name + " unpaused the game"))
        
    # map draw/ping
    if action in (31, 32):
      drawFrom = int(data[2])
      drawType = int(data[3])
      
      # map ping
      if drawType == 0:
        msgStr = None
        if (len(data)) < 14:
          msgStr = decode(data[9:-1])
        else:
          msgStrNew = decode(data[13:-1])
          msgStrOld = decode(data[9:-1])
          isOldBad = any(ord(char) < 32 or ord(char) == 127 for char in msgStrOld)
          isNewBad = any(ord(char) < 32 or ord(char) == 127 for char in msgStrNew)
          
          if isNewBad: msgStr = msgStrOld
          elif isOldBad or not isNewBad : msgStr = msgStrNew
          else: msgStr = msgStrNew
            
        to_index = 253 if (drawFrom in players and getattr(players[drawFrom], 'spectator', 0)) else 252
        
        cache = playerCache.pop(drawFrom, None)
        if msgStr:
          logLines.append((gameTime, drawFrom, to_index, "PING", msgStr))
        else:
          if cache and cache[0] == "PING" and cache[1][-1] > gameTime - 2:
            cache[1].append(gameTime)
          else:
            cache = ("PING", [gameTime])
            logLines.append((gameTime, drawFrom, to_index, "PING", cache))
          playerCache[drawFrom] = cache
          
      # map draw
      elif drawType == 2:
        try:
            if len(data) < 21:
                #OLD REPLAY
                x1: int = struct.unpack("<h", data[4:6])[0]
                z1: int = struct.unpack("<h", data[6:8])[0]
                x2: int = struct.unpack("<h", data[8:10])[0]
                z2: int = struct.unpack("<h", data[10:12])[0]
            else:
                #NEW REPLAY FORMAT
                x1: int = struct.unpack("<h", data[4:6])[0]
                z1: int = struct.unpack("<h", data[8:10])[0]
                x2: int = struct.unpack("<h", data[12:14])[0]
                z2: int = struct.unpack("<h", data[16:18])[0]
                
            SMALL_DRAW_THRESHOLD = 24
            cache_peek = playerCache.get(drawFrom)
            
            # Skip small accidental draws unless part of a sequence
            if abs(x2 - x1) < SMALL_DRAW_THRESHOLD and abs(z2 - z1) < SMALL_DRAW_THRESHOLD:
                if not (cache_peek and cache_peek[0] == "DRAW" and cache_peek[1][-1][0] > gameTime - 5):
                    continue
                    
            cache = playerCache.pop(drawFrom, None)
            if cache and cache[0] == "DRAW" and cache[1][-1][0] > gameTime - 5:
                cache[1].append((gameTime, x1, z1, x2, z2))
            else:
                cache = ("DRAW", [(gameTime, x1, z1, x2, z2)])
                logLines.append((gameTime, drawFrom, 252, "DRAW", cache)) 
            playerCache[drawFrom] = cache
        except: pass

    share_event = extract_share_event(data, players)
    if share_event:
      playerFromShare, playerToShare, shareMessage = share_event
      logLines.append((gameTime, playerFromShare, playerToShare, "SHARE", shareMessage))

  return Summary(
    header=replay.header,
    rawScript=replay.rawSetupScript,
    game=game,
    players=players,
    startTime=startTime,
    logLines=logLines,
    winningAllyTeams=replay.winningAllyTeams,
  )
