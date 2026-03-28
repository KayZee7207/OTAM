import struct
import datetime
import re
import gzip
import io
from typing import NamedTuple, IO

def parseScript(script: str):
  stack = [{}]
  tag = None
  tagIndex = None
  for l in script.split("\n"):
    l = l.strip()
    if not l: continue
    if l.startswith("["):
      m = re.match(r"^\[([a-zA-Z]+)([0-9]+)?\]$", l)
      if m:
        tag = m.group(1)
        tagIndex = int(m.group(2)) if m.group(2) else None
        continue
    elif l == "{":
      if tag is None:
        raise Exception("unexpected script line %r without tag declaration" % (l))
      elif tagIndex is None:
        if tag in stack[-1]:
          raise Exception("duplicate script tag %r" % (tag))
        params = {}
        stack[-1][tag] = params
        stack.append(params)
        continue
      else:
        if tag not in stack[-1]:
          stack[-1][tag] = []
        elif not isinstance(stack[-1][tag], list):
          raise Exception("tag %r is not a list" % (tag))
        while tagIndex > len(stack[-1][tag])-1:
          stack[-1][tag].append(None)
        if stack[-1][tag][tagIndex] is not None:
          raise Exception("duplicate script tag %r:%r" % (tag,tagIndex))
        params = {}
        stack[-1][tag][tagIndex] = params
        stack.append(params)
        continue
    elif l == "}":
      if len(stack) <= 1:
        raise Exception("unexpected script line %r without tag declaration" % (l))
      param = stack.pop(-1)
      for tag, array in param.items():
        if isinstance(array, list):
          for tagIndex, p in enumerate(array):
            if p is None:
              raise Exception("missing script tag %r:%r" % (tag,tagIndex))
      continue
    else:
      m = re.match(r"^(\w+)=(.*);$", l)
      if m:
        k = m.group(1)
        if k in stack[-1]:
          raise Exception("duplicate script field %r" % (k))
        v = m.group(2)
        if re.match(r"^[0-9]+$", v):
          v = int(v)
        elif re.match(r"^[0-9]+\.[0-9]+$", v):
          v = float(v)
        elif re.match(r"^[0-9]+\.[0-9]+ [0-9]+\.[0-9]+ [0-9]+\.[0-9]+$", v):
          v = tuple(float(f) for f in v.split(" "))
        stack[-1][k] = v
        continue
    raise Exception("unparsable script line %r" % (l))
  if len(stack) != 1:
    raise Exception("unexpected script end")
  param = stack.pop(-1)
  for tag, array in param.items():
    if isinstance(array, list):
      for tagIndex, p in enumerate(array):
        if p is None:
          raise Exception("missing script tag %r:%r" % (tag,tagIndex))
  return param

class Header(NamedTuple):
  version: int
  headerSize: int
  versionString: str
  gameID: str
  unixTime: datetime.datetime
  scriptSize: int
  demoStreamSize: int
  gameTime: int
  wallclockTime: int
  numPlayers: int
  playerStatSize: int
  playerStatElemSize: int
  numTeams: int
  teamStatSize: int
  teamStatElemSize: int
  teamStatPeriod: int
  winningAllyTeamsSize: int

class Replay(NamedTuple):
  header: Header
  rawSetupScript: str
  setupScript: dict
  chunks: list[tuple[float, bytes]]
  winningAllyTeams: list[int]

def readReplayHeader(f: IO):
  def read_string(size: int):
    return f.read(size).split(b'\x00')[0].decode()

  def read_int() -> int:
    return struct.unpack("<i", f.read(4))[0]
  
  def read_ts():
    return datetime.datetime.fromtimestamp(struct.unpack("<Q", f.read(8))[0])

  magic = read_string(16)
  if magic != "spring demofile":
    raise Exception("not a spring demofile: %r" % (magic))
  
  version = read_int()
  headerSize = read_int()
  versionString = read_string(256)
  gameID = f.read(16).hex()
  unixTime = read_ts()
  scriptSize = read_int()
  demoStreamSize = read_int()
  gameTime = read_int()
  wallclockTime = read_int()
  numPlayers = read_int()
  playerStatSize = read_int()
  playerStatElemSize = read_int()
  numTeams = read_int()
  teamStatSize = read_int()
  teamStatElemSize = read_int()
  teamStatPeriod = read_int()
  winningAllyTeamsSize = read_int()

  rawSetupScript = read_string(scriptSize)
  setupScript = parseScript(rawSetupScript)

  return Replay(
    header=Header(
      version=version,
      headerSize=headerSize,
      versionString=versionString,
      gameID=gameID,
      unixTime=unixTime,
      scriptSize=scriptSize,
      demoStreamSize=demoStreamSize,
      gameTime=gameTime,
      wallclockTime=wallclockTime,
      numPlayers=numPlayers,
      playerStatSize=playerStatSize,
      playerStatElemSize=playerStatElemSize,
      numTeams=numTeams,
      teamStatSize=teamStatSize,
      teamStatElemSize=teamStatElemSize,
      teamStatPeriod=teamStatPeriod,
      winningAllyTeamsSize=winningAllyTeamsSize,
    ),
    rawSetupScript=rawSetupScript,
    setupScript=setupScript,
    chunks=[],
    winningAllyTeams=[],
  )

def readReplayChunks(f: IO):
  chunks: list[tuple[float, bytes]] = []
  while True:
    header = f.read(8)
    if len(header) < 8: break
    gameTime: float = struct.unpack("<f", header[0:4])[0]
    length: int = struct.unpack("<I", header[4:8])[0]
    if length == 0: continue
    data = f.read(length)
    if len(data) < length: break
    chunks.append((gameTime, data))
  return chunks

def parseWinningAllyTeams(raw: bytes, setupScript: dict):
  if not raw:
    return []

  ally_teams = {
    int(team["allyteam"])
    for team in setupScript.get("game", {}).get("team", [])
    if isinstance(team, dict) and "allyteam" in team
  }

  if len(raw) == len(ally_teams) and all(byte in (0, 1) for byte in raw):
    return [idx for idx, won in enumerate(raw) if won]

  if len(raw) % 4 == 0:
    values = []
    for offset in range(0, len(raw), 4):
      value = struct.unpack("<I", raw[offset:offset + 4])[0]
      if value != 0xFFFFFFFF:
        values.append(int(value))
    if values:
      return values

  return [int(value) for value in raw]
  
def readReplay(filename: str, chunks=False):
  with gzip.open(filename, "rb") as f:
    replay = readReplayHeader(f)
    if not chunks: return replay
    demoStream = f.read(replay.header.demoStreamSize)
    footerSize = replay.header.playerStatSize + replay.header.teamStatSize + replay.header.winningAllyTeamsSize
    footer = f.read(footerSize) if footerSize else b""
    winningRaw = footer[-replay.header.winningAllyTeamsSize:] if replay.header.winningAllyTeamsSize else b""
    return Replay(
      **dict(replay._asdict(),
      chunks=readReplayChunks(io.BytesIO(demoStream)),
      winningAllyTeams=parseWinningAllyTeams(winningRaw, replay.setupScript),
      )
    )
