#!/usr/bin/env python
"""
Shop Management System - Quick Setup Script
Run this to initialize the project: python setup.py
"""

import os
import sys
import subprocess

def run_command(cmd, description):
    """Run a shell command and handle errors"""
    print(f"\n{'='*60}")
    print(f"📦 {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print(e.stderr)
        return False

def main():
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║          SHOP MANAGEMENT SYSTEM - SETUP                  ║
    ║              Django + Cyberpunk UI                       ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    
    # Create virtual environment if not exists
    if not os.path.exists('venv'):
        print("🔧 Creating virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', 'venv'])
    
    # Activate venv and install requirements
    if os.name == 'nt':  # Windows
        pip_cmd = 'venv\\Scripts\\pip'
        python_cmd = 'venv\\Scripts\\python'
    else:  # Unix/Mac
        pip_cmd = 'venv/bin/pip'
        python_cmd = 'venv/bin/python'
    
    steps = [
        (f'{pip_cmd} install --upgrade pip', 'Upgrading pip'),
        (f'{pip_cmd} install -r requirements.txt', 'Installing dependencies'),
        (f'{python_cmd} manage.py makemigrations accounts inventory orders', 'Creating migrations'),
        (f'{python_cmd} manage.py migrate', 'Running migrations'),
        (f'{python_cmd} manage.py collectstatic --noinput', 'Collecting static files'),
    ]
    
    for cmd, desc in steps:
        if not run_command(cmd, desc):
            print(f"\n❌ Setup failed at: {desc}")
            sys.exit(1)
    
    # Create superuser prompt
    print(f"\n{'='*60}")
    print("👤 Create admin user?")
    print(f"{'='*60}")
    response = input("Create superuser now? (y/n): ").lower()
    if response == 'y':
        subprocess.run([python_cmd, 'manage.py', 'createsuperuser'])
    
    print(f"\n{'='*60}")
    print("✅ SETUP COMPLETE!")
    print(f"{'='*60}")
    print(f"""
    🚀 To run the server:
       {python_cmd} manage.py runserver
    
    🌐 Access the application:
       http://127.0.0.1:8000/
    
    🔐 Admin panel:
       http://127.0.0.1:8000/admin/
    """)
    
    # Auto-start option
    response = input("\nStart server now? (y/n): ").lower()
    if response == 'y':
        subprocess.run([python_cmd, 'manage.py', 'runserver'])

if __name__ == '__main__':
    main()