#!/usr/bin/env python3
"""
Simple API test without pipecat dependencies.
Tests the event-driven API endpoints directly.
"""

import requests
import json
import time

def test_api_endpoints():
    """Test the API endpoints for event-driven updates."""
    print("🧪 Testing API Endpoints")
    print("=" * 30)
    
    base_url = "http://localhost:7861"
    
    try:
        # Test 1: Health check
        print("🔍 Test 1: Health check...")
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Health check passed")
            health_data = response.json()
            print(f"   Status: {health_data['status']}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("   ❌ API server not running on port 7861")
        print("   💡 Please start the bot.py server first")
        return
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return
    
    # Test 2: Check initial JD status
    print("\n🔍 Test 2: Initial JD status...")
    try:
        response = requests.get(f"{base_url}/api/jd-status", timeout=5)
        print(f"   Response status: {response.status_code}")
        print(f"   Response headers: {dict(response.headers)}")
        print(f"   Response text: '{response.text}'")
        
        if response.status_code == 200:
            if response.text.strip():
                status_data = response.json()
                print("   ✅ Status check passed")
                print(f"   Has new extraction: {status_data.get('hasNewExtraction', False)}")
                print(f"   Extraction counter: {status_data.get('extractionCounter', 0)}")
            else:
                print("   ❌ Empty response body")
        else:
            print(f"   ❌ Status check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Status check error: {e}")
    
    # Test 3: Check JD data
    print("\n📊 Test 3: JD data fetch...")
    try:
        response = requests.get(f"{base_url}/api/jd-data", timeout=5)
        if response.status_code == 200:
            jd_data = response.json()
            print("   ✅ JD data fetch passed")
            print(f"   Success: {jd_data.get('success', False)}")
            if jd_data.get('data'):
                data = jd_data['data']
                print(f"   Title: '{data.get('title', '')}'")
                print(f"   Company: '{data.get('company', '')}'")
                print(f"   Extracted fields: {jd_data.get('extractedFields', [])}")
                print(f"   Is complete: {jd_data.get('isComplete', False)}")
        else:
            print(f"   ❌ JD data fetch failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ JD data fetch error: {e}")
    
    # Test 4: Check status again (after data fetch)
    print("\n🔍 Test 4: Status after data fetch...")
    try:
        response = requests.get(f"{base_url}/api/jd-status", timeout=5)
        if response.status_code == 200:
            status_data = response.json()
            print("   ✅ Status check passed")
            print(f"   Has new extraction: {status_data.get('hasNewExtraction', False)}")
            print(f"   Extraction counter: {status_data.get('extractionCounter', 0)}")
            
            if not status_data.get('hasNewExtraction', True):
                print("   ✅ Extraction flag correctly reset after data fetch")
            else:
                print("   ⚠️ Extraction flag still true (may indicate active extraction)")
        else:
            print(f"   ❌ Status check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Status check error: {e}")
    
    print(f"\n✅ API endpoint tests completed!")
    print(f"💡 To fully test the event-driven system:")
    print(f"   1. Start the bot.py server")
    print(f"   2. Connect the frontend voice client")
    print(f"   3. Speak to trigger extractions")
    print(f"   4. Watch for extraction-complete events in browser console")

if __name__ == "__main__":
    test_api_endpoints()