import sys
import os
import urllib.parse
from otam.web.server import run_server

def main():
    print("Starting OTAM - Overwatch Tool AI Moderation...")
    
    # Check for file argument (Open With...)
    target_url = "http://localhost:7272"
    
    if len(sys.argv) > 1:
        path = sys.argv[1]
        print(f"Opening: {path}")
        if os.path.exists(path):
            # Convert to absolute path
            abs_path = os.path.abspath(path)
            # Encode for URL
            safe_path = urllib.parse.quote(abs_path)
            target_url = f"http://localhost:7272/view/{safe_path}"

    run_server(url=target_url)

if __name__ == "__main__":
    main()
