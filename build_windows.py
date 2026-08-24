#!/usr/bin/env python3
import os
import subprocess
import sys

def main():
    print("========================================================")
    print("       Ratio Desktop — Building Windows Executable")
    print("========================================================")
    
    root_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")
    
    # 1. Build React Frontend Static Bundle
    print("\n[Step 1/2] Compiling Vite React Frontend static assets...")
    try:
        subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True)
        print("✔ React static build completed (frontend/dist created).")
    except Exception as e:
        print(f"❌ Failed to build React frontend: {e}")
        sys.exit(1)
        
    # 2. Run PyInstaller
    print("\n[Step 2/2] Running PyInstaller executable bundle generation...")
    try:
        subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "ratio.spec"], cwd=root_dir, check=True)
        print("✔ Standalone Ratio Windows executable built successfully in 'dist/Ratio/'.")
        print("\nDistribution package ready!")
        print("  Executable: dist/Ratio/Ratio.exe")
        print("  Launcher:   run_ratio_windows.bat")
    except Exception as e:
        print(f"❌ PyInstaller build error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
