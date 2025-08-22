import os
import sys
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

print("Python version:", sys.version)
print("Current working directory:", os.getcwd())
print("__file__:", __file__)

# Try to find .env file in various locations
possible_env_locations = [
    Path(__file__).parent / '.env',  # Same directory as script
    Path(__file__).parent.parent / '.env',  # Parent directory
    Path.cwd() / '.env',  # Current working directory
]

env_path = None
for loc in possible_env_locations:
    if loc.exists():
        env_path = loc
        break

print("\nLooking for .env file:")
for loc in possible_env_locations:
    print(f"- {loc}: {'FOUND' if loc.exists() else 'not found'}")

if env_path:
    print(f"\nLoading .env from: {env_path}")
    load_dotenv(env_path, override=True)
    
    # Print all environment variables (be careful with sensitive data)
    print("\nEnvironment variables:")
    for key, value in os.environ.items():
        if 'GEMINI' in key or 'API' in key or 'KEY' in key:
            print(f"{key} = {'*' * 8} (hidden for security)")
        else:
            print(f"{key} = {value}")
    
    # Test loading through the actual module
    print("\nTesting tag_automator module:")
    try:
        from tag_automator import ObsidianTagAutomator
        print("Successfully imported ObsidianTagAutomator")
        try:
            automator = ObsidianTagAutomator(".")
            print("Successfully initialized ObsidianTagAutomator")
            print(f"Gemini model available: {hasattr(automator, 'gemini_model') and automator.gemini_model is not None}")
        except Exception as e:
            print(f"Error initializing ObsidianTagAutomator: {e}")
            import traceback
            traceback.print_exc()
    except ImportError as e:
        print(f"Error importing tag_automator: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\nError: No .env file found in any expected location!")
    print("Please create a .env file in the project root with your GEMINI_API_KEY")
