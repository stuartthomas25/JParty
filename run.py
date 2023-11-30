from jparty.main import main
import os
import json

# Check if config.json exists
if not os.path.exists('config.json'):
    # If not, create it with a default theme
    with open('config.json', 'w') as f:
        json.dump({'theme': 'default'}, f)

if __name__ == "__main__":
    main()
