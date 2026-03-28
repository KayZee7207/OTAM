# OTAM - Overwatch Tool AI Moderation

OTAM is a powerful replay analysis and moderation tool for Beyond All Reason (BAR). It combines a modern web interface with AI-powered chat analysis to help moderators review matches efficiently.

## Features

* **Modern Web UI:** Browse replays with a clean, responsive interface powered by Tailwind CSS.
* **AI Analysis:** Analyzes in-game chat for severe Code of Conduct violations using the Gemini API.
* **Replay Visualization:** View map draws, pings, and chat logs formatted for easy reading.
* **Efficient Filtering:** Filter chat by team, player, or role.
* **Direct Play:** Launch replays directly from the tool (requires BAR Debug Launcher).

## Setup \& Usage

|Step|Instruction|
|-|-|
|1|**Download** on Github.|
|2|**Install Python** if you haven't already (Python 3.10+ recommended).|
|3 n/a jump to step 5|**Install Dependencies:** `pip install google-generativeai requests`|
|4 n/a jump to step 5|**Configure Secrets:** Create a `secrets.json` file in the root directory with your `GEMINI\\\_API\\\_KEY`.|
|5|**Run:** Execute `python main.py` or use the `runmain.ps1` script. Or click on Start OTAM |
|6|**Access:** Open your browser to [http://localhost:7272](http://localhost:7272).|

## Project Structure

* `otam/`: Main package

  * `core/`: Core logic (Replay parsing, AI analysis, State)
  * `web/`: Web server and templates
  * `utils/`: Helper utilities
* `assets/`: Static CSS and JS files

## Credits

Developed further by **KayZee Overwatch BAR with the extraordinary help of Gabba_Gandalf who made this possible**

## License

This code is developed using BAR main code from https://github.com/beyond-all-reason
The objective its to support and help Overall Moderation Team with this tool.
