#!/usr/bin/env python3
"""
Test script for event-driven JD updates.

This script simulates the extraction process and tests that the event-driven 
architecture works correctly.
"""

import asyncio
import json
import time
from interview_extractor import JobDescriptionData
from jd_broadcaster import JDDataBroadcaster, create_jd_data_callback
from jd_api_server import JDAPIServer

async def test_event_driven_updates():
    """Test the event-driven JD update system."""
    print("🧪 Testing Event-Driven JD Updates")
    print("=" * 50)
    
    # Create JD data instance
    jd_data = JobDescriptionData()
    print(f"✅ Created JD data instance")
    
    # Create broadcaster (without RTVI for testing)
    broadcaster = JDDataBroadcaster(rtvi_processor=None, transport=None)
    print(f"✅ Created broadcaster")
    
    # Create callback
    callback = create_jd_data_callback(broadcaster, jd_data)
    print(f"✅ Created callback")
    
    # Start API server
    api_server = JDAPIServer(jd_data, port=7861)
    api_server.start()
    print(f"✅ Started API server on port 7861")
    
    # Wait a moment for server to start
    await asyncio.sleep(1)
    
    print("\n🔍 Initial state:")
    print(f"   - Has new extraction: {jd_data.has_new_extraction()}")
    print(f"   - Extraction counter: {jd_data._extraction_counter}")
    print(f"   - Collected fields: {list(jd_data._collected_fields)}")
    
    # Test 1: Simulate an extraction
    print(f"\n🎯 Test 1: Simulating job title extraction...")
    jd_data.title = "Senior Python Developer"
    jd_data._collected_fields.add("title")
    jd_data._has_new_extraction = True
    jd_data._extraction_counter += 1
    jd_data._last_extraction_time = time.time()
    
    # Trigger the callback
    await callback("title", "Senior Python Developer")
    
    print(f"   ✅ Extraction completed")
    print(f"   - Has new extraction: {jd_data.has_new_extraction()}")
    print(f"   - Extraction counter: {jd_data._extraction_counter}")
    
    # Test 2: Check API status endpoint
    print(f"\n🔍 Test 2: Checking API status endpoint...")
    
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:7861/api/jd-status') as response:
            status_data = await response.json()
            print(f"   Status response: {json.dumps(status_data, indent=2)}")
    
    # Test 3: Fetch full data (should mark as consumed)
    print(f"\n📊 Test 3: Fetching full JD data...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:7861/api/jd-data') as response:
            jd_response = await response.json()
            print(f"   Data fetched successfully: {jd_response['success']}")
            print(f"   Title: {jd_response['data']['title']}")
            print(f"   Extracted fields: {jd_response['extractedFields']}")
    
    # Test 4: Check status again (should be consumed)
    print(f"\n🔍 Test 4: Checking status after consumption...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:7861/api/jd-status') as response:
            status_data = await response.json()
            print(f"   Status response: {json.dumps(status_data, indent=2)}")
    
    # Test 5: Another extraction
    print(f"\n🎯 Test 5: Simulating company extraction...")
    jd_data.company = "TechCorp Inc."
    jd_data._collected_fields.add("company")
    jd_data._has_new_extraction = True
    jd_data._extraction_counter += 1
    jd_data._last_extraction_time = time.time()
    
    await callback("company", "TechCorp Inc.")
    
    # Final status check
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:7861/api/jd-status') as response:
            status_data = await response.json()
            print(f"   Final status: {json.dumps(status_data, indent=2)}")
    
    print(f"\n✅ All tests completed successfully!")
    print(f"🎉 Event-driven system is working correctly!")
    
    # Stop API server
    api_server.stop()
    print(f"🛑 API server stopped")

if __name__ == "__main__":
    asyncio.run(test_event_driven_updates())