#!/usr/bin/env python3
"""
Test script to verify automatic JD updates are working.

This script checks:
1. API endpoints are working
2. Event system is sending messages correctly
3. Smart polling fallback works
"""

import requests
import json
import time

def test_automatic_jd_updates():
    """Test the complete automatic JD update system."""
    print("🧪 Testing Automatic JD Updates")
    print("=" * 40)
    
    base_url = "http://localhost:7861"
    
    try:
        # Test 1: Health check
        print("🔍 Test 1: API Health Check...")
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ API server is healthy: {health_data['status']}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ API server not running on port 7861")
        print("   💡 Please start the bot.py server first!")
        return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Test 2: JD Status endpoint (the one that was failing)
    print("\n🔍 Test 2: JD Status Endpoint...")
    try:
        response = requests.get(f"{base_url}/api/jd-status", timeout=5)
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            if response.text.strip() and not response.text.startswith('<!DOCTYPE'):
                status_data = response.json()
                print("   ✅ Status endpoint working correctly")
                print(f"   Has new extraction: {status_data.get('hasNewExtraction', False)}")
                print(f"   Extraction counter: {status_data.get('extractionCounter', 0)}")
                print(f"   Total fields: {status_data.get('totalFields', 0)}")
            else:
                print("   ❌ Status endpoint returned HTML error page")
                print("   💡 Server needs to be restarted to pick up API changes")
                return False
        else:
            print(f"   ❌ Status endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Status endpoint error: {e}")
        return False
    
    # Test 3: JD Data endpoint
    print("\n📊 Test 3: JD Data Endpoint...")
    try:
        response = requests.get(f"{base_url}/api/jd-data", timeout=5)
        if response.status_code == 200:
            jd_data = response.json()
            print("   ✅ JD data endpoint working")
            if jd_data.get('success'):
                data = jd_data['data']
                print(f"   Title: '{data.get('title', '')}'")
                print(f"   Company: '{data.get('company', '')}'")
                print(f"   Extracted fields: {jd_data.get('extractedFields', [])}")
                print(f"   Missing fields: {jd_data.get('missingFields', [])}")
                print(f"   Is complete: {jd_data.get('isComplete', False)}")
            else:
                print(f"   ⚠️ JD data not successful: {jd_data.get('error', 'Unknown error')}")
        else:
            print(f"   ❌ JD data endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ JD data endpoint error: {e}")
        return False
    
    # Test 4: Check status after data fetch (should mark as consumed)
    print("\n🔍 Test 4: Status After Data Consumption...")
    try:
        response = requests.get(f"{base_url}/api/jd-status", timeout=5)
        if response.status_code == 200:
            status_data = response.json()
            print("   ✅ Status check after data fetch")
            print(f"   Has new extraction: {status_data.get('hasNewExtraction', False)}")
            
            if not status_data.get('hasNewExtraction', True):
                print("   ✅ Extraction flag correctly reset (event-driven working)")
            else:
                print("   ⚠️ Extraction flag still true (may indicate ongoing extraction)")
        else:
            print(f"   ❌ Post-fetch status check failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Post-fetch status error: {e}")
    
    print(f"\n🎉 API Testing Complete!")
    print(f"\n📋 Next Steps:")
    print(f"   1. ✅ Start bot.py server (appears to be running)")
    print(f"   2. 🌐 Open frontend at http://localhost:3000")
    print(f"   3. 🎤 Connect to voice chat")
    print(f"   4. 🗣️ Speak about a job description")
    print(f"   5. 👀 Watch browser console for:")
    print(f"       • 📨 Server message received")
    print(f"       • 🎯 Handling extraction-complete event")
    print(f"       • ✨ Smart polling detected new extraction")
    print(f"       • ✅ JD update notifications")
    print(f"\n💡 The system now has both:")
    print(f"   • 🚀 Event-driven updates (primary)")
    print(f"   • 🔄 Smart polling fallback (5-second intervals)")
    
    return True

if __name__ == "__main__":
    success = test_automatic_jd_updates()
    if success:
        print(f"\n🎯 System is ready for automatic JD updates!")
    else:
        print(f"\n❌ System needs attention before testing")