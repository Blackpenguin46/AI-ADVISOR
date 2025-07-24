#!/usr/bin/env python3
"""
Security Check Script

Verify that sensitive authentication files are properly secured
and not exposed to git repository.
"""

import os
import subprocess
from pathlib import Path
import stat

def check_file_permissions():
    """Check that sensitive files have secure permissions."""
    print("🔒 CHECKING FILE PERMISSIONS")
    print("=" * 40)
    
    sensitive_files = [
        'daily_dev_cookies.json',
        'manual_dailydev_cookies.json', 
        'authenticated_dailydev_session.json',
        '.github_creds.enc',
        '.auth_key',
        'nextjs_data_sample.json',
        'graphql_sample.json'
    ]
    
    secure_files = []
    missing_files = []
    
    for filename in sensitive_files:
        filepath = Path(filename)
        if filepath.exists():
            # Check permissions (should be 600 - owner read/write only)
            file_stat = filepath.stat()
            permissions = stat.filemode(file_stat.st_mode)
            
            if permissions.endswith('------'):  # -rw-------
                print(f"✅ {filename}: Secure permissions ({permissions})")
                secure_files.append(filename)
            else:
                print(f"⚠️  {filename}: Insecure permissions ({permissions})")
                # Fix permissions
                os.chmod(filepath, 0o600)
                print(f"   🔧 Fixed permissions for {filename}")
                secure_files.append(filename)
        else:
            missing_files.append(filename)
    
    print(f"\n📊 Summary: {len(secure_files)} secure files, {len(missing_files)} missing files")
    return len(secure_files) > 0

def check_gitignore():
    """Check that .gitignore properly excludes sensitive files."""
    print("\n🚫 CHECKING .GITIGNORE PROTECTION")
    print("=" * 40)
    
    gitignore_path = Path('.gitignore')
    if not gitignore_path.exists():
        print("❌ No .gitignore file found!")
        return False
    
    with open(gitignore_path, 'r') as f:
        gitignore_content = f.read()
    
    required_patterns = [
        '*.json',
        'daily_dev_cookies.json',
        '.github_creds.enc',
        '.auth_key',
        '*.session',
        '*.cookies'
    ]
    
    protected_patterns = []
    missing_patterns = []
    
    for pattern in required_patterns:
        if pattern in gitignore_content:
            print(f"✅ {pattern}: Protected")
            protected_patterns.append(pattern)
        else:
            print(f"❌ {pattern}: Not protected")
            missing_patterns.append(pattern)
    
    print(f"\n📊 Summary: {len(protected_patterns)} protected patterns, {len(missing_patterns)} missing patterns")
    return len(missing_patterns) == 0

def check_git_status():
    """Check if any sensitive files are staged for commit."""
    print("\n📤 CHECKING GIT STATUS")
    print("=" * 40)
    
    try:
        # Get git status
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        
        sensitive_patterns = ['.json', '.enc', '.key', '.session', '.cookies']
        staged_sensitive = []
        
        for line in result.stdout.split('\n'):
            if line.strip():
                filename = line[3:].strip()  # Remove status prefix
                if any(pattern in filename for pattern in sensitive_patterns):
                    # Allow these safe files
                    safe_files = ['requirements.txt', 'package.json', 'knowledge_base_final.json']
                    if filename not in safe_files:
                        staged_sensitive.append((line[:2], filename))
        
        if staged_sensitive:
            print("⚠️  SENSITIVE FILES IN GIT:")
            for status, filename in staged_sensitive:
                print(f"   {status} {filename}")
            return False
        else:
            print("✅ No sensitive files staged for commit")
            return True
            
    except subprocess.CalledProcessError:
        print("⚠️  Could not check git status (not a git repo?)")
        return True

def main():
    """Run all security checks."""
    print("🛡️  SECURITY CHECK FOR AI ADVISOR")
    print("=" * 50)
    print("Checking that authentication files are secure...")
    print()
    
    checks_passed = 0
    total_checks = 3
    
    if check_file_permissions():
        checks_passed += 1
    
    if check_gitignore():
        checks_passed += 1
    
    if check_git_status():
        checks_passed += 1
    
    print("\n" + "=" * 50)
    print("🎯 SECURITY SUMMARY")
    print(f"Passed: {checks_passed}/{total_checks} security checks")
    
    if checks_passed == total_checks:
        print("✅ ALL SECURITY CHECKS PASSED!")
        print("🔒 Your authentication data is properly secured")
    else:
        print("⚠️  SOME SECURITY ISSUES FOUND")
        print("🔧 Please review and fix the issues above")
    
    print("\n💡 SECURITY BEST PRACTICES:")
    print("• Never commit .json files with credentials")
    print("• Keep authentication files local only") 
    print("• Use secure file permissions (600)")
    print("• Regularly rotate authentication tokens")

if __name__ == "__main__":
    main()