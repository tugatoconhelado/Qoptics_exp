import os
import subprocess
import sys
from pathlib import Path

def launch():
    # 1. Get the absolute path of your project root
    # This is the folder where THIS launcher script lives.
    project_root = Path(__file__).parent.absolute()
    
    # 2. Setup the Environment
    env = os.environ.copy()
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = str(project_root) + os.pathsep + env["PYTHONPATH"]
    else:
        env["PYTHONPATH"] = str(project_root)

    print(f"Project Root: {project_root}")
    print("Launching qudi...")

    # 3. Call qudi and FORCE the working directory to your project root
    try:
        # We use 'qudi' (the command) and tell it to run INSIDE project_root
        subprocess.run(["qudi"], env=env, cwd=str(project_root), shell=True)
    except Exception as e:
        print(f"Failed to launch qudi: {e}")

if __name__ == "__main__":
    launch()