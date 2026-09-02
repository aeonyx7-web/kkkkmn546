import subprocess
import os
import sys

def run_command(command, cwd=None):
    print(f"===========================================================")
    print(f"Running: {command}")
    if cwd:
        print(f"Directory: {cwd}")
    print(f"===========================================================")
    
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=cwd,
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=True
        )
        process.wait()
        if process.returncode != 0:
            print(f"\n[!] Error: Command '{command}' failed with exit code {process.returncode}")
            sys.exit(process.returncode)
    except Exception as e:
        print(f"\n[!] Exception executing '{command}': {e}")
        sys.exit(1)

def main():
    # Get the absolute path to the directory containing this script
    root_dir = os.path.abspath(os.path.dirname(__file__))
    api_dir = os.path.join(root_dir, "GasStationApi")
    publish_dir = os.path.join(api_dir, "publish")

    print("--- Starting Project Setup and Execution ---")

    # 1. npm install
    run_command("npm install", cwd=root_dir)

    # 2. npm run build
    run_command("npm run build", cwd=root_dir)

    # 3. & 4. cd GasStationApi && dotnet publish
    if not os.path.exists(api_dir):
        print(f"[!] Error: Directory '{api_dir}' does not exist.")
        sys.exit(1)
        
    # Delete obj and bin to prevent StaticWebAssets caching issues
    import shutil
    for folder in ["obj", "bin"]:
        folder_path = os.path.join(api_dir, folder)
        if os.path.exists(folder_path):
            print(f"Cleaning {folder_path}...")
            shutil.rmtree(folder_path, ignore_errors=True)

    run_command("dotnet clean GasStationApi.csproj -c Release", cwd=api_dir)
    run_command("dotnet publish GasStationApi.csproj -c Release -o ./publish /p:CompressWebAssets=false", cwd=api_dir)

    # 5. & 6. cd publish && dotnet GasStationApi.dll
    if not os.path.exists(publish_dir):
        print(f"[!] Error: Directory '{publish_dir}' does not exist.")
        sys.exit(1)
        
    print("\n--- Starting Application ---")
    run_command("dotnet GasStationApi.dll", cwd=publish_dir)

if __name__ == "__main__":
    main()
