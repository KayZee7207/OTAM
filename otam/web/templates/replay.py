from .layout import build_layout
from otam.core.summary import process_replay, Summary, Player
from otam.core.replays import readReplay
from otam.utils.colors import setupTeamColors
import html
import json
from collections import defaultdict

SPECIAL_PLAYER_INDICES = {
  252: "[Allies]",
  253: "[Spectators]",
  254: "[Everyone]",
  255: "[Host]",
}

def build_replay_view(filename: str):
    replay = readReplay(filename, chunks=True)
    summary = process_replay(replay)
    
    # 0. Color Logic Fix: Use Replay data first, fallback to utils
    # If summary.players has rgbcolor, use it.
    player_colors = {}
    
    # Fallback generation just in case
    fallback_colors = setupTeamColors(summary.game)
    
    for pid, p in summary.players.items():
        if pid in fallback_colors:
             player_colors[pid] = fallback_colors[pid]
        elif p.rgbcolor:
            player_colors[pid] = p.rgbcolor
            
    # Also ensure Host/System doesn't break if referenced
    
    # Generate CSS Variables for Player Colors
    colors_css = "".join(f"""
    .player-{pid} {{ --player-color: rgb({r*100}%, {g*100}%, {b*100}%); }}
    """ for pid, (r, g, b) in player_colors.items())
    
    # Override styles
    style = f"<style>{colors_css}</style>"
    
    # 1. Metadata Header
    dt = summary.header.unixTime.isoformat(" ")
    date_part, time_part = dt.split(" ")
    REPLAY_LINK = f"https://www.beyondallreason.info/replays?gameId={summary.header.gameID}"
    winner_labels = [f"Team {ally_team + 1}" for ally_team in summary.winningAllyTeams]
    winner_html = ""
    if winner_labels:
        winner_label = winner_labels[0] if len(winner_labels) == 1 else ", ".join(winner_labels)
        winner_prefix = "Winner" if len(winner_labels) == 1 else "Winners"
        winner_html = f"""
        <div class="h-4 w-px bg-white/10"></div>
        <div class="text-slate-200 text-sm font-semibold">{winner_prefix}: {html.escape(winner_label)}</div>
        """
    
    header_html = f"""
    <div class="flex items-center gap-3 bg-slate-900 rounded-xl px-4 py-3 border border-white/5 shadow-sm mb-6 flex-wrap">
        <div class="flex items-center gap-2 text-slate-300 font-mono text-sm">
            <span class="text-indigo-300 font-bold">{date_part}</span>
            <span class="text-slate-500">|</span>
            <span>{time_part}</span>
        </div>
        <div class="h-4 w-px bg-white/10"></div>
        <div class="text-white font-bold flex items-center gap-2">
            <span class="text-lg">🗺️</span> {html.escape(str(summary.game.get("mapname", "Unknown")))}
        </div>
        {winner_html}
        <div class="flex-grow"></div>
        <button onclick="analyzeReplay('{filename.replace("\\", "\\\\")}')" class="text-sm font-bold text-white bg-indigo-600 px-3 py-1.5 rounded-lg hover:bg-indigo-500 transition-colors flex items-center gap-2 shadow-lg hover:shadow-indigo-500/25 mr-2">
            <span>✨</span> Analyze
        </button>
        <a href="{REPLAY_LINK}" target="_blank" class="text-sm font-medium text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded hover:bg-indigo-500/20 transition-colors">
            BAR Replay Site ↗
        </a>
    </div>
    """
    
    # 2. Collapsible Data
    headers_json = html.escape(json.dumps(dict(summary.header._asdict(), unixTime=summary.header.unixTime.isoformat()), indent=2))
    script_content = html.escape(summary.rawScript)
    
    collapsibles_html = f"""
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div class="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
            <h3 class="collapser p-3 bg-slate-800 text-xs font-bold uppercase text-slate-500 cursor-pointer hover:text-white transition-colors border-b border-slate-700">
                Replay Header [+]
            </h3>
            <pre class="collapsable collapsed p-4 text-xs font-mono text-slate-400 overflow-auto max-h-60 bg-slate-950">{headers_json}</pre>
        </div>
        <div class="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
             <h3 class="collapser p-3 bg-slate-800 text-xs font-bold uppercase text-slate-500 cursor-pointer hover:text-white transition-colors border-b border-slate-700">
                Start Script [+]
            </h3>
            <pre class="collapsable collapsed p-4 text-xs font-mono text-slate-400 overflow-auto max-h-60 bg-slate-950 whitespace-pre-wrap">{script_content}</pre>
        </div>
    </div>
    """
    
    # 3. Process Log Lines (Chat)
    chat_bubbles = []
    pause_counts = defaultdict(int)
    
    def get_player_name(idx):
        if idx in summary.players: return html.escape(summary.players[idx].name)
        return html.escape(SPECIAL_PLAYER_INDICES.get(idx, ""))

    for gameTime, playerFrom, playerTo, lineType, msgStr in summary.logLines:
        seconds = abs(gameTime - summary.startTime)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        timeStr = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}" if hours else f"{int(minutes):02d}:{int(seconds):02d}"
        if gameTime < summary.startTime: timeStr = "-" + timeStr

        playerFromName = get_player_name(playerFrom)
        playerToName = get_player_name(playerTo)

        # Layout Logic
        alignment = "justify-start"
        bg_color = "bg-slate-700/50"
        flex_dir = "flex-row"
        
        if playerFrom in summary.players:
            if summary.players[playerFrom].allyteam == 1: # Team 2 (Red usually)
                alignment = "justify-end"
                flex_dir = "flex-row-reverse"
        # System messages
        if playerFrom == 255 or lineType in ["JOINED", "LEFT", "PAUSE", "SHARE"]:
             # Event Highlighting Logic
             msg_text = str(msgStr)
             
             # Fix Player Join/Left Name Details
             if lineType in ["JOINED", "LEFT"]:
                  if playerFrom in summary.players:
                      pName = summary.players[playerFrom].name
                      if pName not in msg_text:
                          msg_text = f"{pName} {msg_text}" # e.g. "PlayerName Player left: Resigned"
             
             # Pause Counter Logic
             if lineType == "PAUSE" and "paused the game" in msg_text:
                 # Try to identify who paused. Usually message is "Name paused the game"
                 # But we also have playerFrom if it's not 255. 
                 # Wait, summary.py line 115 sets playerFrom to 255 for pauses!
                 # But the message string starts with player_name.
                 # Let's rely on the playerFrom tracking if possible, or parse name.
                 # summary.py: logLines.append((gameTime, 255, None, "PAUSE", player_name + " paused the game"))
                 # We don't have the ID easily here unless we parse name back to ID or trust name.
                 # However, existing pause logic allows counting based on name string or just appending.
                 
                 # Let's extract name. "X paused the game".
                 pauser_name = msg_text.replace(" paused the game", "")
                 # We can just count by name string since ID is lost (255)
                 pause_counts[pauser_name] += 1
                 count = pause_counts[pauser_name]
                 msg_text = f"{msg_text} ({count})"

             # Default Style
             evt_bg = "bg-slate-800"
             evt_text = "text-slate-400"
             evt_border = "border-slate-700"
             
             lower_msg = msg_text.lower()
             
             # Highlight Logic
             if "vote" in lower_msg:
                 if "cancelled" in lower_msg or "failed" in lower_msg:
                     evt_bg = "bg-red-900/20"
                     evt_text = "text-red-400"
                     evt_border = "border-red-500/30"
                 elif "passed" in lower_msg:
                     evt_bg = "bg-green-900/20"
                     evt_text = "text-green-400"
                     evt_border = "border-green-500/30"
                 else: # Active/Called vote
                     evt_bg = "bg-yellow-900/20"
                     evt_text = "text-amber-400"
                     evt_border = "border-amber-500/30"
             elif "resign" in lower_msg: 
                 evt_bg = "bg-red-900/30"
                 evt_text = "text-red-300 font-bold"
                 evt_border = "border-red-500/50"
             elif "joined" in lower_msg:
                 evt_text = "text-blue-400 font-bold" # Boosted visibility
             elif "left" in lower_msg:
                 evt_text = "text-orange-400 font-bold"
             elif "pause" in lower_msg:
                 evt_bg = "bg-sky-900/30"
                 evt_text = "text-sky-300 font-bold"
                 evt_border = "border-sky-500/50"
             elif "shared" in lower_msg and ("metal" in lower_msg or "energy" in lower_msg):
                 evt_bg = "bg-emerald-900/30"
                 evt_text = "text-emerald-300 font-bold"
                 evt_border = "border-emerald-500/50"
             
             chat_bubbles.append(f"""
                <div class="flex justify-center my-2 opacity-90 text-xs group player-{playerFrom}">
                    <span class="{evt_bg} {evt_text} px-3 py-1 rounded-full border {evt_border} flex items-center gap-2 shadow-sm">
                        <span class="font-mono opacity-60">{timeStr}</span>
                        <span>{html.escape(msg_text)}</span>
                    </span>
                </div>
             """)
             continue

        # Content Rendering (Pings/Draws)
        content_html = ""
        if isinstance(msgStr, tuple):
             if msgStr[0] == "PING":
                 ping_count = len(msgStr[1])
                 
                 # v2.3 Logic: Color Thresholds
                 # White < 30
                 # Yellow 30-49
                 # Red 50+
                 
                 color_class = "text-slate-200" # White-ish
                 size_class = "text-sm"
                 
                 if ping_count >= 50:
                     color_class = "text-red-500 animate-pulse font-black"
                     size_class = "text-4xl" # Keep some impact sizing
                 elif ping_count >= 30:
                     color_class = "text-yellow-400 font-bold"
                     size_class = "text-2xl"
                 else:
                     # Normal/White
                     color_class = "text-slate-200"
                     size_class = "text-base"
                     if ping_count > 5: size_class = "text-lg" # Slight bump
                     
                 content_html = f'<span class="{color_class} {size_class} flex items-center gap-2 transition-all">🔔 <span>PING</span> <span class="text-xs opacity-70 font-mono bg-black/30 px-1 rounded">x{ping_count}</span></span>'
        
             elif msgStr[0] == "DRAW":
                 # Draw rendering logic
                 all_x, all_z = [], []
                 for _, x1, z1, x2, z2, *rest in msgStr[1]:
                     all_x.extend([x1, x2])
                     all_z.extend([z1, z2])
                 
                 if all_x:
                     min_x, max_x = min(all_x), max(all_x)
                     min_z, max_z = min(all_z), max(all_z)
                     width, height = max_x - min_x, max_z - min_z
                     padding = max(width, height) * 0.1 + 50
                     
                     # Normalize viewbox
                     width += padding * 2
                     height += padding * 2
                     min_x -= padding
                     min_z -= padding
                     
                     if width > height:
                         min_z -= (width - height) / 2
                         height = width
                     else:
                         min_x -= (height - width) / 2
                         width = height
                     
                     lines_svg = "".join(f'<path d="M{x1} {z1} L{x2} {z2}" stroke="currentColor" stroke-width="{width/50}" stroke-linecap="round" />' for _, x1, z1, x2, z2, *rest in msgStr[1])
                     
                     content_html = f"""
                     <div class="mt-1">
                        <div class="bg-slate-900 rounded border border-slate-600 inline-block overflow-hidden relative">
                             <div class="absolute inset-0 opacity-20 bg-[url('https://www.beyondallreason.info/images/maps/Comet_Catcher_Redux.jpg')] bg-cover bg-center"></div>
                             <svg viewBox="{min_x} {min_z} {width} {height}" class="w-48 h-48 text-white relative z-10 opacity-90 fill-none">
                                {lines_svg}
                             </svg>
                        </div>
                        <div class="text-[10px] text-slate-500 mt-0.5 font-mono">MAP DRAW</div>
                     </div>
                     """
                 else:
                     content_html = "Empty Draw"
        else:
            # String based messages
            if lineType == "PING":
                 # PING MESSAGE Event
                 # We need to track the count. Since we are inside the loop, we need a counter initialized outside or reuse pause_counts (bad name) or new dict.
                 # Let's use a new key in pause_counts or a specific ping_msg_counts. 
                 # Since I cannot modify initialization easily in this chunk without being extremely invasive (StartLine),
                 # I will hack it by checking if it exists in local logic or just using a unique key in the existing default dict if possible?
                 # Actually, I am modifying the loop body, so I can't init a NEW var outside.
                 # However, `pause_counts` is available. I can use a composite key like `f"ping_msg_{playerFrom}"`.
                 
                 count_key = f"ping_msg_{playerFrom}"
                 pause_counts[count_key] += 1
                 count = pause_counts[count_key]
                 
                 content_html = f'''
                 <div class="flex flex-col gap-1">
                    <span class="text-yellow-400 font-bold flex items-center gap-2 text-sm">
                        🔔 <span>PING MESSAGE</span> 
                        <span class="text-xs opacity-70 font-mono bg-black/30 px-1 rounded">x{count}</span>
                    </span>
                    <span class="text-slate-200">{html.escape(str(msgStr))}</span>
                 </div>
                 '''
            else:
                 content_html = html.escape(str(msgStr))
            
        # Avatar Logic
        # Priority: Country Code via Image -> Name Initials -> "??"
        BAR_REPO_RAW = "https://raw.githubusercontent.com/beyond-all-reason/Beyond-All-Reason/master/luaui/images/advplayerslist"
        avatar_content = "??"
        
        if playerFrom in summary.players:
            p = summary.players[playerFrom]
            if p.countrycode and p.countrycode != "NCC":
                 country_url = f"{BAR_REPO_RAW}/flags/{p.countrycode.lower()}.png"
                 avatar_content = f'<img src="{country_url}" class="w-full h-full object-cover opacity-90">'
            elif playerFromName:
                 avatar_content = playerFromName[:2].upper()
                 
        elif playerFromName:
              avatar_content = playerFromName[:2].upper()

        # Bubble HTML
        chat_bubbles.append(f"""
        <div class="flex {alignment} mb-1 group player-{playerFrom} w-full">
            <div class="flex {flex_dir} gap-2 max-w-[85%] items-start">
                <div class="flex-shrink-0 mt-0.5">
                    <div class="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-[10px] shadow-sm border border-slate-600 overflow-hidden" style="background-color: var(--player-color); filter: brightness(0.9);">
                        {avatar_content}
                    </div>
                </div>
                <div class="{bg_color} px-3 py-2 rounded-2xl text-slate-200 shadow-sm border border-slate-700/50 group-hover:border-slate-600 transition-colors text-sm min-w-[200px]">
                    <div class="flex items-baseline gap-2 flex-wrap mb-1">
                        <span class="font-bold text-xs" style="color: var(--player-color); filter: brightness(1.2);">{playerFromName}</span>
                        {f'<span class="text-[10px] bg-slate-800/50 px-1 rounded text-slate-400">to {playerToName}</span>' if playerToName and playerToName != playerFromName else ''}
                        <span class="text-[10px] text-slate-500 font-mono">{timeStr}</span>
                    </div>
                    <div class="leading-snug break-words">
                        {content_html}
                    </div>
                </div>
            </div>
        </div>
        """)
        
    # 3. Analysis Results Placeholder
    # Placed here to be below Headers/Script but above Chat
    analysis_html = """
    <div id="analysisResults" style="display:none" class="mb-6 bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-lg animate-fade-in">
        <!-- JS will populate this -->
    </div>
    """
    
    # 4. Filter Sidebar Logic
    playersByTeam = defaultdict(list)
    for player in summary.players.values():
        if player.allyteam is None:
            sort_key = 999 
            team_key = "spectators"
            team_name = "[Spectators]"
        else:
            sort_key = player.allyteam
            team_key = f"team-{player.allyteam}"
            team_name = f"[Team {player.allyteam + 1}]"
            
        playersByTeam[(sort_key, team_key, team_name)].append(player)
        
    filters_html = []
    
    # CSS to handle filtering
    filter_css = "<style>"
    
    # Sort by the explicit sort_key we added (0, 1, ... 999)
    # Add System/Host entry manually if needed, usually they don't appear in 'players' unless mapped.
    # We will handle Host messages (255) as a separate filter.
    
    # Resources
    BAR_REPO_RAW = "https://raw.githubusercontent.com/beyond-all-reason/Beyond-All-Reason/master/luaui/images/advplayerslist"
    
    filter_css += """
    #chat-container.deselected-filter-host .player-255 { display: none !important; }
    """
    
    filters_html.append("""
    <div class="mb-4">
      <h4 class="text-xs font-bold uppercase text-slate-500 mb-2 tracking-wider flex items-center">
         <input type="checkbox" value="filter-host" checked class="mr-2 accent-indigo-500" onchange="updateFilter(this)" /> [System/Host]
      </h4>
    </div>
    """)

    for (sort_idx, cls, name), players in sorted(playersByTeam.items()):
        
        team_filters = []
        for p in players:
            filter_css += f"#chat-container.deselected-filter-player-{p.index} .player-{p.index} {{ display: none !important; }}\n"
            
            # Format: Country | Rank | Skill | Name
            # Country Image
            country_html = '<span class="text-slate-600">??</span>'
            if p.countrycode and p.countrycode != "NCC":
                 country_url = f"{BAR_REPO_RAW}/flags/{p.countrycode.lower()}.png"
                 country_html = f'<img src="{country_url}" alt="{p.countrycode}" class="w-4 h-3 object-cover rounded-[1px] shadow-sm" title="{p.countrycode}">'
            
            # Rank Image
            rank_html = '<span class="text-slate-600">-</span>'
            if p.rank is not None:
                rank_url = f"{BAR_REPO_RAW}/ranks/{p.rank}.png"
                rank_html = f'<img src="{rank_url}" alt="R{p.rank}" class="w-3.5 h-3.5 object-contain" title="Rank {p.rank}">'

            skill_val = p.skill if p.skill else "-"

            team_filters.append(f"""
            <label class="player-{p.index} filter-player inline-flex items-center px-2 py-1.5 rounded bg-slate-800 border border-slate-700 cursor-pointer hover:bg-slate-700 transition-colors text-xs w-full mb-1" data-id="{p.id}" data-name="{html.escape(p.name)}">
              <input type="checkbox" class="parent-filter-{cls} mr-1.5 accent-indigo-500" value="filter-player-{p.index}" checked onchange="updateFilter(this)" />
              <div class="flex-grow truncate flex items-center gap-1 text-[10px] text-slate-400">
                  {country_html}
                  <span class="opacity-10">|</span>
                  {rank_html}
                  <span class="opacity-10">|</span>
                  <span title="Skill" class="font-mono">{skill_val}</span>
                  <span class="opacity-10">|</span>
                  <span class="font-bold text-xs truncate" style="color: var(--player-color); filter: brightness(1.2);">{html.escape(p.name)}</span>
              </div>
            </label>
            """)
            
        filters_html.append(f"""
        <div class="mb-4">
          <h4 class="text-xs font-bold uppercase text-slate-500 mb-2 tracking-wider flex items-center">
             <input type="checkbox" value="filter-{cls}" checked class="mr-2 accent-indigo-500" onchange="toggleTeamFilters(this, '{cls}')" /> {name}
          </h4>
          <div class="pl-2">
            {"".join(team_filters)}
          </div>
        </div>
        """)
        
    filter_css += "</style>"
    
    script = """
    <script>
    function updateFilter(checkbox) {
        const target = document.getElementById('chat-container');
        const filterClass = 'deselected-' + checkbox.value;
        if (checkbox.checked) target.classList.remove(filterClass);
        else target.classList.add(filterClass);
    }
    
    function toggleTeamFilters(parentCheckbox, teamClass) {
        const inputs = document.querySelectorAll('.parent-filter-' + teamClass);
        inputs.forEach(input => {
            input.checked = parentCheckbox.checked;
            updateFilter(input);
        });
    }
    </script>
    """
    
    content = f"""
    {style}
    {filter_css}
    {header_html}
    {collapsibles_html}
    {analysis_html}
    
    <div class="flex flex-col lg:flex-row gap-6">
      <!-- Sidebar -->
      <div class="lg:w-80 flex-shrink-0">
          <div class="bg-slate-900 p-4 rounded-xl border border-slate-800 sticky top-24 max-h-[calc(100vh-8rem)] overflow-y-auto custom-scrollbar">
            <h3 class="text-sm font-bold text-white mb-4 uppercase tracking-wider border-b border-slate-800 pb-2">Filters</h3>
            {"".join(filters_html)}
          </div>
      </div>
    
      <!-- Chat Feed -->
      <div class="flex-grow" id="chat-container">
          <div class="bg-slate-900 rounded-xl border border-slate-800 p-6 min-h-[500px]">
             {script}
             {"".join(chat_bubbles)}
          </div>
      </div>
    </div>
    """
    
    return build_layout(filename, content, title=f"Replay - {summary.game.get('mapname', 'Unknown')}")
