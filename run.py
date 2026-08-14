#!/usr/bin/env python3
"""
Student Result Management System - Main Application Runner
"""

import os
import sys
from app import app, create_default_data

def main():
    print("=" * 60)
    print("STUDENT RESULT MANAGEMENT SYSTEM")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("ERROR: Python 3.7 or higher is required!")
        sys.exit(1)
    
    print(f"Python Version: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    
    try:
        # Create default data
        print("\nInitializing database...")
        create_default_data()
        
        print("\n" + "=" * 60)
        print("Starting Flask application...")
        print("Application URL: http://localhost:5000")
        print("\nDefault Login Credentials:")
        print("  Admin:    username='admin'    password='admin123'")
        print("  Teacher:  username='teacher'  password='teacher123'")
        print("\nStudent Login: Use roll number and date of birth")
        print("=" * 60)
        print("\nPress CTRL+C to stop the server\n")
        
        # Run the application
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Check if you have write permissions in the current directory")
        print("2. Try running as administrator")
        print("3. Check if SQLite is installed")
        print("4. Make sure no other program is using port 5000")
        sys.exit(1)

if __name__ == '__main__':
    main()