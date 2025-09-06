#!/usr/bin/env python3
"""
Test script for JD integration functionality
"""

import json
import asyncio
from interview_extractor import JDData, JDExtractor
from jd_api_server import JDAPIServer
from jd_broadcaster import JDDataBroadcaster, create_jd_data_callback


async def test_jd_data_functionality():
    """Test the JD data extraction and conversion functionality."""
    print("🧪 Testing JD Data Integration")
    
    # Test 1: Basic JD Data functionality
    print("\n1. Testing JDData basic functionality...")
    jd_data = JDData()
    
    # Test field updates
    await jd_data.update_field("job_title", "Senior React Developer")
    await jd_data.update_field("company_name", "TechCorp Inc")
    await jd_data.update_field("salary_range", "$120,000 - $150,000")
    await jd_data.update_field("technical_skills", ["React", "TypeScript", "Node.js"])
    await jd_data.update_field("required_qualifications", "5+ years of experience\nBachelor's degree preferred")
    await jd_data.update_field("work_arrangement", "Remote-friendly")
    await jd_data.update_field("employment_type", "Full-time")
    
    print(f"✅ Collected fields: {jd_data.get_collected_fields()}")
    print(f"✅ Missing fields: {jd_data.get_missing_fields()}")
    print(f"✅ Is complete: {jd_data.is_complete()}")
    
    # Test 2: Frontend format conversion
    print("\n2. Testing frontend format conversion...")
    frontend_data = jd_data.to_frontend_format()
    print("✅ Frontend format:")
    print(json.dumps(frontend_data, indent=2))
    
    # Test 3: Test callback mechanism
    print("\n3. Testing callback mechanism...")
    callback_triggered = False
    
    def test_callback(field_name, field_value):
        nonlocal callback_triggered
        callback_triggered = True
        print(f"✅ Callback triggered: {field_name} = {field_value}")
    
    jd_data.add_update_callback(test_callback)
    await jd_data.update_field("responsibilities", "Lead frontend development team")
    
    if callback_triggered:
        print("✅ Callback mechanism working correctly")
    else:
        print("❌ Callback mechanism failed")
    
    # Test 4: API Server (basic functionality)
    print("\n4. Testing API Server...")
    try:
        api_server = JDAPIServer(jd_data, port=7862)  # Use different port for testing
        api_server.start()
        print("✅ API Server started successfully")
        
        # Give it a moment to start
        await asyncio.sleep(1)
        
        api_server.stop()
        print("✅ API Server stopped successfully")
    except Exception as e:
        print(f"⚠️ API Server test failed: {e}")
    
    print("\n🎉 JD Integration Tests Completed!")
    print(f"📊 Final stats: {len(jd_data.get_collected_fields())}/{len(jd_data.get_all_fields())} fields collected")


if __name__ == "__main__":
    asyncio.run(test_jd_data_functionality())