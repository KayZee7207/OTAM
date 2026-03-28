import sys
import os

# Add current directory to path so we can import lib
sys.path.append(os.getcwd())

try:
    from lib import ai_analysis
    print("Import successful")
    result = ai_analysis.analyze_chat_logs([])
    print("Function call successful:", result)
except Exception as e:
    print("Error:", e)
