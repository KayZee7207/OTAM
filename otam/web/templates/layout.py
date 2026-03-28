import os
import pathlib

CODE_OF_CONDUCT_URL = "https://www.beyondallreason.info/code-of-conduct#section-a-be-nice-to-each-other"

def build_layout(filename: str, content: str, title="OTAM"):
  """
  Generates the full HTML page with the header (breadcrumbs) and provided content.
  """
  path_html = build_breadcrumbs(filename)
  
  return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    
    <!-- Utilities -->
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- Config -->
    <script>
      tailwind.config = {{
        darkMode: ['class', '[data-theme="dark"]'],
        theme: {{
          extend: {{
            fontFamily: {{ sans: ['Inter', 'sans-serif'] }},
            colors: {{
              slate: {{ 850: '#1e293b', 900: '#0f172a', 950: '#020617' }}
            }}
          }}
        }}
      }}
    </script>
    
    <!-- Static Assets -->
    <link rel="stylesheet" href="/assets/style.css">
    <script src="/assets/script.js" defer></script>
  </head>
  <body class="bg-slate-900 text-white min-h-screen">
      
    <!-- Header / Navbar -->
    {path_html}

    <!-- Main Content -->
    <div id="mainContent" class="max-w-[1800px] mx-auto px-4 py-6">
      {content}
    </div>
    
    <!-- Settings Modal -->
    <div id="settingsModal" style="display:none;" class="fixed inset-0 bg-black/50 z-[1500] flex justify-center items-center">
      <div class="bg-slate-900 text-white w-[95%] max-w-lg p-6 rounded-xl border border-white/10 relative shadow-2xl">
        <button id="settingsClose" class="absolute top-3 right-3 text-slate-400 hover:text-white">✕</button>
        <h2 class="text-xl font-bold mb-4">Settings</h2>
        
        <div class="mb-4">
          <label class="block mb-2 text-sm text-slate-400">Chat Font Size</label>
          <select id="fontSizeSelector" class="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white outline-none focus:border-indigo-500 transition-colors">
            <option value="12">Tiny</option>
            <option value="14">Small</option>
            <option value="16">Normal (Default)</option>
            <option value="18">Large</option>
            <option value="20">Huge</option>
            <option value="custom">Custom...</option>
          </select>
          <div id="customFontSizeInputContainer" class="hidden mt-2">
             <div class="flex items-center gap-2">
                 <input type="number" id="customFontSizeInput" placeholder="14" class="bg-slate-950 border border-slate-700 rounded p-2 text-white text-sm w-full outline-none focus:border-indigo-500" />
                 <span class="text-slate-500 text-xs">px</span>
             </div>
          </div>
        </div>
        
        <div class="mb-4">
          <label class="block mb-2 text-sm text-slate-400">Max Width</label>
          <select id="widthSelector" class="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white outline-none focus:border-indigo-500 transition-colors">
            <option value="1800px">Full (Default)</option>
            <option value="1600px">Large (1600px)</option>
            <option value="1400px">Medium (1400px)</option>
            <option value="1200px">Narrow (1200px)</option>
            <option value="1000px">Focused (1000px)</option>
            <option value="custom">Custom...</option>
          </select>
          <div id="customWidthGroup" class="mt-2 flex gap-2 hidden">
             <input type="text" id="customWidthInput" placeholder="e.g. 90% or 1500px" class="flex-grow bg-slate-800 border border-slate-700 rounded p-2 text-white text-sm outline-none focus:border-indigo-500 transition-colors" />
             <button id="applyCustomWidth" class="bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1 rounded text-sm font-bold transition-colors">OK</button>
          </div>
        </div>

        <div class="border-t border-white/10 mt-6 pt-4 text-xs text-slate-500 flex justify-between">
          <div>OTAM v2.2.1</div>
          <div>Developed further by KayZee Overwatch BAR with the extraordinary help of Gabba_Gandalf who made this possible | March 2026</div>
        </div>
      </div>
    </div>

    <!-- Context Menu Placeholder -->
    <div class="context-menu" id="contextFilterMenu"></div>
  </body>
</html>
"""

def build_breadcrumbs(filename: str):
  # Normalize path
  filenameToSend = filename.replace("\\", "//")
  pathItems = [pathlib.Path(filename)]
  while True:
    last = pathItems[-1]
    if last.parent == last: break
    pathItems.append(last.parent)

  if os.name != "posix":
    try:
        pathItems.append(pathlib.Path(str(pathItems[-1].drive)))
    except: pass # drive might not exist

  path_links_html = []
  for index, item in reversed(list(enumerate(pathItems))):
      if item.name or (item.drive and index == len(pathItems) - 1):
          name = item.name or item.drive
          url = "/view/" + str(item).replace("\\", "/").strip("/")
          
          separator = '<svg class="w-3.5 h-3.5 text-slate-600 mx-1 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>'
          pill_class = "px-2 py-0.5 rounded hover:bg-white/10 transition-colors truncate max-w-[150px] sm:max-w-xs block cursor-pointer"
          
          if index == 0: # Active
              path_links_html.append(f'{separator}<span class="{pill_class} text-indigo-200 font-medium bg-indigo-500/10" title="{name}">{name}</span>')
          else:
              path_links_html.append(f'{separator}<a href="{url}" class="{pill_class} !bg-indigo-500/10 !text-indigo-200 hover:!bg-indigo-500/20 hover:!text-indigo-100" title="{name}">{name}</a>')
  
  path_links_str = "".join(path_links_html)
  
  # Buttons
  icon_btn = "h-9 w-9 flex items-center justify-center rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 border border-transparent hover:border-slate-700 transition-all"
  primary_btn = "h-9 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium shadow-lg shadow-indigo-500/20 transition-all flex items-center gap-2 hover:scale-105 active:scale-95 border border-indigo-500"
  
  start_replay_btn = ""
  analyze_btn = ""
  
  if os.name != "posix" and ".sdfz" in filename:
      start_replay_btn = f"""
      <button onclick="runReplay('{filenameToSend}')" class="{primary_btn} bg-emerald-600 hover:bg-emerald-500 border-emerald-500 shadow-emerald-500/20">
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"></path></svg>
        Play
      </button>
      """
      analyze_btn = ""

  return f"""
<div id="path" class="sticky top-0 z-50 bg-slate-950 border-b border-white/5 shadow-2xl">
  <div class="max-w-[1800px] mx-auto px-4 h-16 flex justify-between items-center gap-4">
    
    <!-- Branding -->
    <a href="{CODE_OF_CONDUCT_URL}" target="_blank" rel="noopener noreferrer" class="flex-shrink-0 flex items-center justify-center rounded-xl overflow-hidden border border-indigo-500/20 bg-black shadow-lg shadow-indigo-500/10">
        <img src="/assets/bar-coc-menu.png" alt="BAR Code of Conduct" class="h-10 w-auto block">
    </a>

    <!-- Address Bar -->
    <div class="flex-grow max-w-4xl mx-4">
        <div class="flex items-center bg-slate-900 rounded-xl px-3 py-1.5 border border-white/5 shadow-inner overflow-hidden focus-within:ring-2 focus-within:ring-indigo-500/30 transition-all">
            <a href="/" class="p-1 rounded !bg-indigo-500/10 !text-indigo-200 hover:!bg-indigo-500/20 transition-colors flex-shrink-0">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"></path></svg>
            </a>
            
            <div class="flex items-center text-sm font-medium whitespace-nowrap overflow-x-auto no-scrollbar mask-linear-fade px-2 w-full">
                {path_links_str}
            </div>
            
            <button onclick="openSelectPath()" class="ml-2 p-1 rounded hover:bg-white/10 text-slate-500 hover:text-white transition-colors flex-shrink-0">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
            </button>
        </div>
    </div>

    <!-- Toolbar -->
    <div class="flex items-center gap-2 flex-shrink-0">
        {start_replay_btn}
        {analyze_btn}
        <div class="h-6 w-px bg-white/10 mx-2"></div>
        <button id="settingsButton" class="{icon_btn}" title="Settings">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
        </button>
    </div>
  </div>
</div>
"""
