"""
HumAL Installer
Automatically detects CUDA and installs the appropriate PyTorch version.
"""
import subprocess
import sys
import re
import platform

def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def get_package_manager():
    """Detect if uv is available, otherwise fall back to pip"""
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            return 'uv'
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return 'pip'

def get_cuda_version():
    """Detect CUDA version from nvidia-smi or nvcc"""
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            match = re.search(r'CUDA Version: (\d+)\.(\d+)', result.stdout)
            if match:
                major, minor = match.groups()
                return f"{major}.{minor}", int(major), int(minor)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    try:
        result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            match = re.search(r'release (\d+)\.(\d+)', result.stdout)
            if match:
                major, minor = match.groups()
                return f"{major}.{minor}", int(major), int(minor)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return None, None, None

def get_torch_index_url(cuda_major, cuda_minor):
    """Get the appropriate PyTorch index URL based on CUDA version"""
    if cuda_major is None:
        return None, None
    
    # CUDA 13.x - use CUDA 13.0 wheels
    if cuda_major == 13:
        return "https://download.pytorch.org/whl/cu130", "cu130"
    # CUDA 12.x - prefer 12.8, fallback to 12.6 for older 12.x versions
    elif cuda_major == 12:
        if cuda_minor >= 8:
            return "https://download.pytorch.org/whl/cu128", "cu128"
        elif cuda_minor >= 6:
            return "https://download.pytorch.org/whl/cu126", "cu126"
        else:
            # Older CUDA 12.x versions use cu121 for compatibility
            return "https://download.pytorch.org/whl/cu121", "cu121"
    # CUDA 11.8+
    elif cuda_major == 11 and cuda_minor >= 8:
        return "https://download.pytorch.org/whl/cu118", "cu118"
    # CUDA 11.x (older than 11.8)
    elif cuda_major == 11:
        return "https://download.pytorch.org/whl/cu118", "cu118"
    else:
        print(f"⚠️  Warning: CUDA {cuda_major}.{cuda_minor} detected but may not be supported by PyTorch.")
        print(f"    Falling back to CPU-only installation.")
        return None, None

def install_pytorch(force_cpu=False, package_manager='pip'):
    """Install PyTorch with CUDA support if available"""
    print_header("PyTorch Installation")
    
    if force_cpu:
        print("💻 CPU-only installation requested")
        cuda_version, cuda_major, cuda_minor = None, None, None
    else:
        print("🔍 Detecting CUDA installation...")
        cuda_version, cuda_major, cuda_minor = get_cuda_version()
    
    if cuda_version and not force_cpu:
        print(f"✓ CUDA {cuda_version} detected")
        index_url, cuda_tag = get_torch_index_url(cuda_major, cuda_minor)
        
        if index_url:
            print(f"📦 Installing PyTorch with CUDA {cuda_tag} support...")
            print(f"   Using: {package_manager}")
            
            if package_manager == 'uv':
                cmd = ["uv", "pip", "install", "torch", "--index-url", index_url, "--upgrade", "--force-reinstall"]
            else:
                cmd = [sys.executable, "-m", "pip", "install", "torch", "--index-url", index_url, "--upgrade", "--force-reinstall"]
            
            try:
                subprocess.run(cmd, check=True)
                print(f"✓ PyTorch with CUDA {cuda_tag} installed successfully")
                return True
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install PyTorch with CUDA: {e}")
                print(f"   Falling back to CPU-only installation...")
        else:
            print("⚠️  CUDA detected but no compatible PyTorch build found")
    else:
        if not force_cpu:
            print("ℹ️  No CUDA installation detected")
    
    # CPU-only installation
    print("📦 Installing CPU-only PyTorch...")
    if package_manager == 'uv':
        cmd = ["uv", "pip", "install", "torch", "--upgrade", "--force-reinstall"]
    else:
        cmd = [sys.executable, "-m", "pip", "install", "torch", "--upgrade", "--force-reinstall"]
    
    try:
        subprocess.run(cmd, check=True)
        print("✓ CPU-only PyTorch installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install PyTorch: {e}")
        return False

def install_dependencies(package_manager='pip'):
    """Install dependencies from requirements.txt"""
    print_header("Installing Dependencies")
    
    print(f"📦 Installing dependencies from requirements.txt...")
    print(f"   Using: {package_manager}")
    
    if package_manager == 'uv':
        cmd = ["uv", "pip", "install", "-r", "requirements.txt"]
    else:
        cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    
    try:
        subprocess.run(cmd, check=True)
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def verify_installation():
    """Verify that PyTorch is installed and working"""
    print_header("Verifying Installation")
    
    try:
        import torch
        print(f"✓ PyTorch version: {torch.__version__}")
        
        if torch.cuda.is_available():
            print(f"✓ CUDA is available")
            print(f"  - CUDA version: {torch.version.cuda}")
            print(f"  - GPU device: {torch.cuda.get_device_name(0)}")
            print(f"  - GPU count: {torch.cuda.device_count()}")
        else:
            print("ℹ️  CUDA not available - running on CPU")
            print("   For GPU support, run: python install.py --reinstall-torch")
        
        return True
    except ImportError:
        print("❌ PyTorch not found - installation may have failed")
        return False
    except Exception as e:
        print(f"⚠️  Error during verification: {e}")
        return False

def main():
    """Main installation flow"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Install HumAL with automatic CUDA detection")
    parser.add_argument("--cpu-only", action="store_true", help="Force CPU-only PyTorch installation")
    parser.add_argument("--reinstall-torch", action="store_true", help="Only reinstall PyTorch (skip other dependencies)")
    parser.add_argument("--skip-torch", action="store_true", help="Skip PyTorch installation")
    parser.add_argument("--use-pip", action="store_true", help="Force use of pip instead of uv")
    
    args = parser.parse_args()
    
    print_header(f"HumAL Installer")
    print(f"Python: {sys.version}")
    print(f"Platform: {platform.platform()}")
    
    # Detect package manager
    if args.use_pip:
        package_manager = 'pip'
        print("📦 Using pip (forced)")
    else:
        package_manager = get_package_manager()
        print(f"📦 Detected package manager: {package_manager}")
    
    success = True
    
    # Install dependencies unless we're only reinstalling torch
    if not args.reinstall_torch:
        if not install_dependencies(package_manager=package_manager):
            success = False
    
    # Install PyTorch unless explicitly skipped
    if not args.skip_torch:
        if not install_pytorch(force_cpu=args.cpu_only, package_manager=package_manager):
            success = False
    
    # Verify installation
    if not args.skip_torch:
        if not verify_installation():
            success = False
    
    # Final summary
    print_header("Installation Complete" if success else "Installation Completed with Warnings")
    
    if success:
        print("✓ HumAL is ready to use!")
        print("\nNext steps:")
        print("  Double click the start-dev.bat file to start the development environment.")
    else:
        print("⚠️  Installation completed with some issues.")
        print("    Please review the errors above and try again.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())