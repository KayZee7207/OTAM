import sys
import os
from lib.replays import readReplay

def analyze(filename):
    print(f"--- Analyzing {filename} ---")
    try:
        replay = readReplay(filename, chunks=True)
        
        ping_count = 0
        draw_count = 0
        
        for gameTime, data in replay.chunks:
            action = int(data[0])
            if action == 32:
                drawType = int(data[3])
                if drawType == 0:
                    if ping_count < 3:
                        print(f"PING (Type 0): len={len(data)} data={data.hex()}")
                    ping_count += 1
                elif drawType == 2:
                    draw_count += 1
        
        print(f"Total Pings: {ping_count}, Total Draws: {draw_count}")
            
    except Exception as e:
        print(f"Error reading {filename}: {e}")

if __name__ == "__main__":
    analyze("demos/AFTER BAR UPDATE.sdfz")
