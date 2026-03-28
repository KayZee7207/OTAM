from .layout import build_layout
import pathlib
from otam.core import state
from otam.core.replays import readReplay
import html
import traceback

def build_home(dir_path: str):
  dirobj = pathlib.Path(dir_path)
  
  current_state = state.load_state()

  subdirs = [subdir for subdir in dirobj.iterdir() if subdir.is_dir()]
  replayFiles = sorted(
      (file for file in dirobj.iterdir() if file.is_file() and file.suffix == ".sdfz"), key=lambda p: p.stat().st_ctime, reverse=True)

  # Subdirectories HTML
  subdirs_html = ""
  if subdirs:
      cards = "".join(f"""
        <a href="/view/{str(subdir).removeprefix('/')}" class="block p-4 bg-slate-800 rounded-lg border border-slate-700 hover:bg-slate-700 hover:border-indigo-500 transition-all duration-200 group">
            <div class="flex items-center">
                <span class="text-2xl mr-3 group-hover:scale-110 transition-transform">📂</span>
                <span class="font-medium text-slate-200 group-hover:text-white truncate">{subdir.name}</span>
            </div>
        </a>
      """ for subdir in subdirs)
      
      subdirs_html = f"""
        <div id="subdirs" class="mb-8">
          <h3 class="collapser text-xl font-bold mb-4 flex items-center cursor-pointer text-slate-200 hover:text-white transition-colors">
            <span class="mr-2">📁</span> Subdirectories [{'+' if replayFiles else '-'}]
          </h3>
          <div class="collapsable grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {cards}
          </div>
        </div>
      """

  # Replays HTML
  replays_html = ""
  if replayFiles:
      cards = []
      for file in replayFiles:
          try:
            replay = readReplay(str(file), chunks=False)
            game = replay.setupScript["game"]
            
            # Analysis Status
            analysis = current_state.get(file.name)
            is_analyzed = analysis is not None
            toxicity_score = analysis.get("toxicity_score", 0) if analysis else 0
            
            badge_color = "bg-green-500"
            if toxicity_score > 7: badge_color = "bg-red-600"
            elif toxicity_score > 4: badge_color = "bg-yellow-500"
            elif toxicity_score == 0 and is_analyzed: badge_color = "bg-green-500"
            
            duration = replay.header.wallclockTime
            hours, duration = divmod(duration, 3600)
            minutes, seconds = divmod(duration, 60)
            durationStr = f"{hours}h {minutes:02d}m" if hours else f"{minutes:02d}m {seconds:02d}s"

            filename_escaped = str(file).replace("\\", "//")
            map_name = html.escape(str(game.get("mapname", "Unknown Map")))
            player_count = len(game.get("player", []))
            
            analyzed_badge = ""
            if is_analyzed:
                analyzed_badge = f"""
                <div class="absolute top-2 right-2 {badge_color} text-white text-xs font-bold px-2 py-1 rounded-full shadow-lg z-10">
                    SCORE: {toxicity_score}
                </div>
                """

            cards.append(f"""
            <div class="relative bg-slate-800 rounded-xl overflow-hidden shadow-lg border border-slate-700 hover:border-indigo-500 transition-all duration-300 hover:shadow-2xl hover:-translate-y-1 group replay-card" data-analyzed="{str(is_analyzed).lower()}">
                {analyzed_badge}
                <div class="h-32 bg-gradient-to-br from-slate-700 to-slate-900 flex items-center justify-center relative overflow-hidden">
                    <span class="relative z-10 text-4xl opacity-50 group-hover:scale-110 transition-transform">🗺️</span>
                    <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-slate-900 to-transparent p-2">
                        <p class="text-xs text-slate-300 font-mono truncate text-center">{map_name}</p>
                    </div>
                </div>
                
                <div class="p-4">
                    <div class="flex justify-between items-start mb-2">
                        <h4 class="text-sm font-bold text-white truncate w-full" title="{file.name}">{file.name}</h4>
                    </div>
                    
                    <div class="flex justify-between text-xs text-slate-400 mb-4">
                        <span class="flex items-center"><span class="mr-1">⏱️</span> {durationStr}</span>
                        <span class="flex items-center"><span class="mr-1">👥</span> {player_count} Players</span>
                    </div>
                    
                    <div class="flex gap-2 mt-2">
                        <button onclick="runReplay('{filename_escaped}')" class="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold py-2 px-3 rounded transition-colors flex items-center justify-center">
                            <span class="mr-1">▶️</span> Play
                        </button>
                        <a href="/view/{str(file).removeprefix('/')}" class="flex-1 bg-slate-700 hover:bg-slate-600 text-white text-xs font-bold py-2 px-3 rounded transition-colors text-center flex items-center justify-center">
                            <span class="mr-1">🔍</span> View
                        </a>
                    </div>
                </div>
            </div>
            """)
          except Exception:
              cards.append(f'<div class="bg-red-900/20 p-4 rounded text-red-500">Failed: {file.name}</div>')
              
      replays_html = f"""
      <div>
          <div class="flex justify-between items-center mb-6">
              <h3 class="text-2xl font-bold text-white flex items-center">
                <span class="mr-2">📼</span> Replays
                <span class="ml-3 text-sm font-normal text-slate-400 bg-slate-800 px-3 py-1 rounded-full">{len(replayFiles)} files</span>
              </h3>
              <button id="toggleAnalyzedBtn" onclick="toggleAnalyzed()" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-2 rounded border border-slate-700 transition-colors flex items-center">
                  <span class="mr-2">👁️</span> Hide Analyzed
              </button>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-6">
            {"".join(cards)}
          </div>
      </div>
      """

  content = subdirs_html + replays_html
  return build_layout(dir_path, content)
