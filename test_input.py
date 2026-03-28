import msvcrt
import time

print("Press 'q' to quit. Press any other key to see its code.")

while True:
    if msvcrt.kbhit():
        key = msvcrt.getch()
        print(f"Key pressed: {key}")
        if key.lower() == b'q':
            print("Quitting...")
            break
    time.sleep(0.1)
