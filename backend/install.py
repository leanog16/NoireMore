#!/usr/bin/env python3
"""
One-click installer for Fact Checker Backend
Installs all dependencies automatically
"""

import subprocess
import sys

def install_package(package):
    """Install a single package"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '--quiet'])
        return True
    except:
        return False

def main():
    print("🚀 Fact Checker Backend Installer")
    print("=" * 50)
    
    packages = [
        'flask',
        'flask-cors', 
        'requests',
        'beautifulsoup4'
    ]
    
    success_count = 0
    failed_packages = []
    
    for package in packages:
        print(f"\n📦 Installing {package}...", end=" ")
        if install_package(package):
            print("✓")
            success_count += 1
        else:
            print("✗")
            failed_packages.append(package)
    
    print("\n" + "=" * 50)
    
    if success_count == len(packages):
        print("✅ All dependencies installed successfully!")
        print("\n🎯 Next steps:")
        print("   1. Run: python app.py")
        print("   2. Open: http://localhost:5000")
        print("   3. Test: python test_api.py")
    else:
        print(f"⚠️  {len(failed_packages)} package(s) failed to install:")
        for pkg in failed_packages:
            print(f"   - {pkg}")
        print("\n💡 Try running:")
        print("   pip install flask flask-cors requests beautifulsoup4")
        print("\nOr with system packages:")
        print("   pip install flask flask-cors requests beautifulsoup4 --break-system-packages")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()