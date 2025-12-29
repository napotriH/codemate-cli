#!/usr/bin/env python3
import subprocess
import sys
import os

def main():
    # Gaseste directorul unde se afla scriptul
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cli_main_path = os.path.join(script_dir, "cli_main.py")
    
    # Ruleaza CodeMate CLI
    try:
        subprocess.run([sys.executable, cli_main_path], cwd=script_dir)
    except KeyboardInterrupt:
        print("\nCodeMate CLI stopped.")
    except Exception as e:
        print(f"Error starting CodeMate CLI: {e}")

if __name__ == "__main__":
    main()