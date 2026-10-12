import subprocess
import sys
import os
import json
import platform
from typing import List, Dict, Optional
from pathlib import Path

class GhostSnapInstaller:
    """
    Auto Requirements Installer for GhostSnap.
    Checks environment, installs missing dependencies, and verifies success.
    Handles pip detection, virtual environments, and permission errors.
    """

    def __init__(self):
        self.required_packages = [
            "aiohttp",
            "requests",
            "python-dotenv"  # Optional for future config
        ]
        self.python_executable = sys.executable
        self.is_windows = platform.system().lower() == "windows"
        self.is_venv = self._check_virtualenv()

    def _check_virtualenv(self) -> bool:
        """Check if running inside a virtual environment."""
        return (
            hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        )

    def _get_pip_command(self) -> List[str]:
        """Determine the correct pip command for the current environment."""
        if self.is_venv:
            return [self.python_executable, "-m", "pip"]
        return [sys.executable, "-m", "pip"]

    def check_installed_packages(self) -> Dict[str, bool]:
        """Check which required packages are already installed."""
        installed = {}
        pip_cmd = self._get_pip_command()
        
        try:
            result = subprocess.run(
                pip_cmd + ["list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                installed_data = json.loads(result.stdout)
                installed_names = {pkg["name"].lower() for pkg in installed_data}
                for package in self.required_packages:
                    installed[package] = package.lower() in installed_names
            else:
                print(f"[-] Failed to list installed packages: {result.stderr}")
                for package in self.required_packages:
                    installed[package] = False
        except Exception as e:
            print(f"[-] Error checking packages: {e}")
            for package in self.required_packages:
                installed[package] = False
        
        return installed

    def install_package(self, package: str) -> bool:
        """Install a single package using pip."""
        pip_cmd = self._get_pip_command()
        cmd = pip_cmd + ["install", package]
        
        print(f"[*] Installing {package}...")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout per package
            )
            
            if result.returncode == 0:
                print(f"[+] Successfully installed {package}")
                return True
            else:
                print(f"[-] Failed to install {package}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"[-] Timeout while installing {package}")
            return False
        except Exception as e:
            print(f"[-] Error installing {package}: {e}")
            return False

    def install_all_requirements(self) -> bool:
        """Main installation routine."""
        print(f"[*] Python: {self.python_executable}")
        print(f"[*] Virtual Environment: {'Yes' if self.is_venv else 'No'}")
        print(f"[*] OS: {platform.system()} {platform.release()}")
        print("-" * 50)
        
        installed_status = self.check_installed_packages()
        missing_packages = [pkg for pkg, is_installed in installed_status.items() if not is_installed]
        
        if not missing_packages:
            print("[+] All requirements already installed!")
            return True
        
        print(f"[*] Missing packages: {', '.join(missing_packages)}")
        
        success_count = 0
        for package in missing_packages:
            if self.install_package(package):
                success_count += 1
        
        print("-" * 50)
        if success_count == len(missing_packages):
            print("[+] All requirements installed successfully!")
            return True
        else:
            print(f"[-] Failed to install {len(missing_packages) - success_count} packages")
            return False

    def verify_installation(self) -> bool:
        """Verify that all required packages can be imported."""
        print("[*] Verifying installation...")
        all_good = True
        
        for package in self.required_packages:
            try:
                __import__(package)
                print(f"[+] {package} verified")
            except ImportError:
                print(f"[-] {package} failed to import")
                all_good = False
        
        return all_good

    def create_requirements_file(self):
        """Create a requirements.txt file for future reference."""
        requirements_path = Path("requirements.txt")
        if not requirements_path.exists():
            with open(requirements_path, "w") as f:
                for package in self.required_packages:
                    f.write(f"{package}\n")
            print("[+] Created requirements.txt")

def main():
    print("=" * 50)
    print("GhostSnap Auto Requirements Installer")
    print("=" * 50)
    
    installer = GhostSnapInstaller()
    
    # Install all requirements
    if installer.install_all_requirements():
        # Verify installation
        if installer.verify_installation():
            print("\n[+] Environment ready for GhostSnap!")
            installer.create_requirements_file()
        else:
            print("\n[-] Installation completed but verification failed")
            sys.exit(1)
    else:
        print("\n[-] Installation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
