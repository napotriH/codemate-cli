import os
import sys
import shutil
from pathlib import Path

def install_codemate():
    """Instaleaza CodeMate CLI ca o comanda globala"""
    
    # Directorul curent (unde se afla CodeMate)
    current_dir = Path(__file__).parent.absolute()
    
    # Calea catre Python Scripts (unde se pun comenzile globale)
    python_scripts = Path(sys.executable).parent / "Scripts"
    
    if not python_scripts.exists():
        print(f"Python Scripts directory not found: {python_scripts}")
        return False
    
    # Copiaza fisierele necesare
    try:
        # Copiaza launcher-ul
        shutil.copy2(current_dir / "codemate.py", python_scripts / "codemate.py")
        shutil.copy2(current_dir / "codemate.bat", python_scripts / "codemate.bat")
        
        # Copiaza toate fisierele CLI
        cli_files = ["cli_main.py", "cli_agent.py", "requirements.txt"]
        for file in cli_files:
            if (current_dir / file).exists():
                shutil.copy2(current_dir / file, python_scripts / file)
        
        print("✅ CodeMate CLI installed successfully!")
        print("You can now use 'codemate' command from anywhere!")
        print("\nUsage:")
        print("  codemate    - Start CodeMate CLI")
        
        return True
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

if __name__ == "__main__":
    install_codemate()