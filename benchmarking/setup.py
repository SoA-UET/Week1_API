#!/usr/bin/env python3
"""
Setup script for API Benchmarking Suite
Helps with environment setup and dependency management
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, cwd=None, description=None):
    """Run a command and handle errors"""
    if description:
        print(f"⚙️  {description}")
    
    try:
        result = subprocess.run(
            command.split() if isinstance(command, str) else command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ Success: {description or command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {description or command}")
        print(f"Error: {e.stderr}")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Dependencies...")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found!")
        return False
    
    return run_command(
        f"{sys.executable} -m pip install -r {requirements_file}",
        description="Installing Python packages"
    )

def generate_grpc_files():
    """Generate gRPC protobuf files"""
    print("🔧 Generating gRPC protobuf files...")
    
    grpc_dir = Path(__file__).parent / "app" / "gRPC"
    proto_file = grpc_dir / "proto" / "user_service.proto"
    
    if not proto_file.exists():
        print("❌ user_service.proto not found!")
        return False
    
    # Generate protobuf files
    command = [
        sys.executable, "-m", "grpc_tools.protoc",
        f"--proto_path={proto_file.parent}",
        f"--python_out={grpc_dir}",
        f"--grpc_python_out={grpc_dir}",
        str(proto_file)
    ]
    
    return run_command(
        command,
        cwd=str(grpc_dir),
        description="Generating protobuf files"
    )

def check_python_version():
    """Check Python version compatibility"""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. Current version: {version.major}.{version.minor}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def create_reports_directory():
    """Create reports directory if it doesn't exist"""
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    print(f"📁 Reports directory ready: {reports_dir}")

def verify_data_file():
    """Verify the users.csv data file exists"""
    data_file = Path(__file__).parent / "app" / "common" / "data" / "users.csv"
    
    if not data_file.exists():
        print(f"❌ Data file not found: {data_file}")
        return False
    
    # Count lines
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
        print(f"✅ Data file ready with {line_count} users")
        return True
    except Exception as e:
        print(f"❌ Error reading data file: {e}")
        return False

def run_quick_test():
    """Run a quick test to verify everything works"""
    print("🧪 Running quick test...")
    
    # Try importing main modules
    try:
        sys.path.append(str(Path(__file__).parent / "app"))
        
        from common.utils import DataLoader
        from common.models import User
        
        # Test data loading
        data_file = Path(__file__).parent / "app" / "common" / "data" / "users.csv"
        loader = DataLoader(str(data_file))
        users = loader.load_users(5)  # Load just 5 users for test
        
        if len(users) > 0:
            print(f"✅ Successfully loaded {len(users)} test users")
            print(f"   Sample user: {users[0].name} ({users[0].email})")
            return True
        else:
            print("❌ No users loaded from CSV")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 API Benchmarking Suite Setup")
    print("=" * 50)
    
    success_count = 0
    total_checks = 6
    
    # Run setup steps
    steps = [
        ("Python Version Check", check_python_version),
        ("Install Dependencies", install_dependencies),
        ("Generate gRPC Files", generate_grpc_files),
        ("Create Reports Directory", create_reports_directory),
        ("Verify Data File", verify_data_file),
        ("Quick Test", run_quick_test)
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}")
        if step_func():
            success_count += 1
        else:
            print(f"❌ {step_name} failed")
    
    print(f"\n📊 Setup Results: {success_count}/{total_checks} steps completed")
    
    if success_count == total_checks:
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("  • Run all benchmarks: python benchmark.py")
        print("  • Run specific APIs: python benchmark.py --apis REST GraphQL")
        print("  • See README.md for more options")
    else:
        print("⚠️  Setup completed with issues. Check the errors above.")
        print("You may still be able to run benchmarks, but some features might not work.")
    
    return success_count == total_checks

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)