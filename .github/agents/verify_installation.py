#!/usr/bin/env python3
"""
Installation Verification Script
Checks that all components of the Code Review Agent are properly installed.
"""

import sys
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text.center(70)}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def check_files():
    """Check that all required files exist."""
    print_header("Checking File Structure")
    
    required_files = [
        ".github/agents/mythos.CRA.agent.md",
        ".github/agents/README.md",
        ".github/agents/SETUP_GUIDE.md",
        ".github/agents/ARCHITECTURE.md",
        ".github/agents/QUICK_REFERENCE.md",
        ".github/agents/tools/__init__.py",
        ".github/agents/tools/complexity_analyzer.py",
        ".github/agents/tools/security_linter.py",
        ".github/agents/tools/codespace_file_reader.py",
        ".github/agents/tools/demo.py",
        ".github/agents/tools/test_tools.py",
        ".github/agents/tools/README.md",
        ".github/agents/tools/requirements.txt",
        "requirements.txt"
    ]
    
    all_exist = True
    for filepath in required_files:
        full_path = Path(filepath)
        if full_path.exists():
            print_success(f"{filepath}")
        else:
            print_error(f"{filepath} - NOT FOUND")
            all_exist = False
    
    return all_exist

def check_dependencies():
    """Check that required Python packages are installed."""
    print_header("Checking Python Dependencies")
    
    required_packages = {
        'radon': '6.0.1',
        'bandit': '1.7.10',
        'pydantic': '2.10.5'
    }
    
    all_installed = True
    for package, version in required_packages.items():
        try:
            __import__(package)
            print_success(f"{package} - Installed")
        except ImportError:
            print_error(f"{package}~={version} - NOT INSTALLED")
            all_installed = False
    
    return all_installed

def check_tool_imports():
    """Check that all tools can be imported."""
    print_header("Checking Tool Imports")
    
    sys.path.insert(0, str(Path('.github/agents')))
    
    tools = [
        'tools.complexity_analyzer',
        'tools.security_linter',
        'tools.codespace_file_reader'
    ]
    
    all_importable = True
    for tool in tools:
        try:
            __import__(tool)
            print_success(f"{tool}")
        except Exception as e:
            print_error(f"{tool} - {e}")
            all_importable = False
    
    return all_importable

def test_tools():
    """Run basic tests on each tool."""
    print_header("Testing Tool Functionality")
    
    sys.path.insert(0, str(Path('.github/agents')))
    
    # Test complexity analyzer
    try:
        from tools.complexity_analyzer import complexity_analyzer
        result = complexity_analyzer("def test(): return 1")
        if 'error' not in result:
            print_success("complexity_analyzer - Working")
        else:
            print_error(f"complexity_analyzer - {result['error']}")
    except Exception as e:
        print_error(f"complexity_analyzer - {e}")
    
    # Test security linter
    try:
        from tools.security_linter import security_linter
        result = security_linter("def test(): return 1")
        if 'error' not in result:
            print_success("security_linter - Working")
        else:
            print_error(f"security_linter - {result['error']}")
    except Exception as e:
        print_error(f"security_linter - {e}")
    
    # Test file reader
    try:
        from tools.codespace_file_reader import codespace_file_reader
        result = codespace_file_reader("manage.py")
        if 'error' not in result:
            print_success("codespace_file_reader - Working")
        else:
            print_warning(f"codespace_file_reader - {result.get('details', result['error'])}")
    except Exception as e:
        print_error(f"codespace_file_reader - {e}")

def print_summary(files_ok, deps_ok, imports_ok):
    """Print final summary."""
    print_header("Installation Summary")
    
    if files_ok and deps_ok and imports_ok:
        print_success("✨ All components are properly installed!")
        print_success("✨ The Code Review Agent is ready to use!")
        print(f"\n{GREEN}Next Steps:{RESET}")
        print("  1. Run the demo: python .github/agents/tools/demo.py manage.py")
        print("  2. Run tests: python -m pytest .github/agents/tools/test_tools.py -v")
        print("  3. Review documentation: cat .github/agents/README.md")
        return True
    else:
        print_error("⚠️  Some components are missing or not working properly")
        print(f"\n{YELLOW}Action Required:{RESET}")
        
        if not deps_ok:
            print("  • Install dependencies: pip install -r requirements.txt")
        
        if not files_ok:
            print("  • Some files are missing - please check the file structure")
        
        if not imports_ok:
            print("  • Tool imports failed - check PYTHONPATH or dependencies")
        
        return False

def main():
    """Main verification workflow."""
    print(f"{BLUE}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║         CODE REVIEW AGENT - INSTALLATION VERIFICATION             ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{RESET}")
    
    files_ok = check_files()
    deps_ok = check_dependencies()
    imports_ok = check_tool_imports()
    test_tools()
    
    success = print_summary(files_ok, deps_ok, imports_ok)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
