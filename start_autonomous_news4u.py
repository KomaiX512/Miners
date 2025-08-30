#!/usr/bin/env python3
"""
AUTONOMOUS NEWS4U STARTUP SCRIPT
Simple script to start the autonomous News4U system with different modes.
"""

import sys
import os
import subprocess
import argparse

def main():
    """Main startup function with user-friendly options."""
    parser = argparse.ArgumentParser(
        description='Start the Autonomous News4U System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_autonomous_news4u.py --production    # Start production mode (24-hour loop)
  python start_autonomous_news4u.py --test         # Start test mode (2-minute loop)
  python start_autonomous_news4u.py --test-account instagram emelie_pakistan
  python start_autonomous_news4u.py --status       # Show system status
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--production', action='store_true', 
                      help='Run in production mode (24-hour processing intervals)')
    group.add_argument('--test', action='store_true',
                      help='Run in test mode (2-minute processing intervals)')
    group.add_argument('--test-account', nargs=2, metavar=('PLATFORM', 'USERNAME'),
                      help='Test processing for a single account')
    group.add_argument('--status', action='store_true',
                      help='Show system status and exit')
    
    args = parser.parse_args()
    
    # Build command
    cmd = [sys.executable, 'autonomous_news4u_system.py']
    
    if args.production:
        print("🚀 Starting Autonomous News4U System in PRODUCTION mode")
        print("⏰ Processing interval: 24 hours")
        print("🔄 System will loop continuously until stopped with Ctrl+C")
        print()
        # No additional flags needed for production mode
        
    elif args.test:
        print("🧪 Starting Autonomous News4U System in TEST mode")
        print("⏰ Processing interval: 2 minutes")
        print("🔄 System will loop continuously until stopped with Ctrl+C")
        print()
        cmd.append('--test')
        
    elif args.test_account:
        platform, username = args.test_account
        print(f"🎯 Testing single account: {platform}:{username}")
        print()
        cmd.extend(['--test', '--single', platform, username])
        
    elif args.status:
        print("🔍 Checking Autonomous News4U System status...")
        print()
        cmd.append('--status')
    
    try:
        # Execute the command
        result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n🛑 System stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error starting system: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
