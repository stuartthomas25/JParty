from jparty.main import main
import time
import os
import json
import subprocess
import signal

# Check if config.json exists
if not os.path.exists('config.json'):
    # If not, create it with a default theme
    with open('config.json', 'w') as f:
        json.dump({'theme': 'default'}, f)

if __name__ == "__main__":
    print(os.getcwd())
    # Start the process and get the process object
    process = subprocess.Popen(["python", "..\\pibuzzers\\physicalbuzzers.py"])
    time.sleep(1)
    try:
        main()
    finally:
        # When the user quits the game, terminate the process
        process.terminate()
        try:
            # Ensure process is terminated
            process.wait(timeout=0.2)
        except subprocess.TimeoutExpired:
            # Force kill if process did not terminate
            os.kill(process.pid, signal.SIGKILL)