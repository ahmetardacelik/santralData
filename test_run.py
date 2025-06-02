#!/usr/bin/env python3
"""
Simple test script for EPIAS app
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

try:
    print("🧪 Testing imports...")
    
    # Test Flask
    from flask import Flask
    print("✅ Flask import successful")
    
    # Test other dependencies
    import requests
    print("✅ Requests import successful")
    
    import pandas
    print("✅ Pandas import successful")
    
    import openpyxl
    print("✅ OpenPyXL import successful")
    
    # Test our modules
    from epias_extractor import EpiasExtractor
    print("✅ EpiasExtractor import successful")
    
    from app import app
    print("✅ Flask app import successful")
    
    # Test basic app creation
    test_client = app.test_client()
    
    with app.app_context():
        # Test API endpoints
        print("\n🌐 Testing endpoints...")
        
        response = test_client.get('/api/health')
        if response.status_code == 200:
            print("✅ Health endpoint working")
            data = response.get_json()
            print(f"   Status: {data.get('status')}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
        
        response = test_client.get('/api')
        if response.status_code == 200:
            print("✅ API info endpoint working")
        else:
            print(f"❌ API info endpoint failed: {response.status_code}")
    
    print("\n✅ All tests passed! The system should work correctly.")
    print("\n🚀 You can now run:")
    print("   python run.py dev    # Development mode")
    print("   python run.py prod   # Production mode")
    print("   python run.py docker # Docker mode")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\n💡 Please install requirements:")
    print("   pip install -r requirements.txt")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 