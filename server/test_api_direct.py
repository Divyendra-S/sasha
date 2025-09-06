#!/usr/bin/env python3
"""
Test script to verify API server data updates
"""

import asyncio
import requests
import time
from interview_extractor import JDData
from jd_api_server import JDAPIServer


async def test_api_updates():
    """Test that API server reflects data updates immediately."""
    print("🧪 Testing API Server Real-Time Updates")
    
    # Create JD data and API server
    jd_data = JDData()
    api_server = JDAPIServer(jd_data, port=7862)  # Use different port
    
    try:
        # Start API server
        api_server.start()
        await asyncio.sleep(2)  # Give server time to start
        
        # Test initial state
        response = requests.get('http://localhost:7862/api/jd-data')
        if response.ok:
            initial_data = response.json()
            print("✅ Initial API state:", initial_data['data']['title'])
        
        # Update JD data
        print("\n🔄 Updating job title...")
        await jd_data.update_field("job_title", "Senior React Developer")
        
        # Check API immediately
        time.sleep(0.5)  # Small delay
        response = requests.get('http://localhost:7862/api/jd-data')
        if response.ok:
            updated_data = response.json()
            print("✅ Updated API state:", updated_data['data']['title'])
            
            if updated_data['data']['title'] == "Senior React Developer":
                print("🎉 API server correctly reflects data updates!")
            else:
                print("❌ API server not reflecting updates")
                print("Expected: Senior React Developer")
                print("Got:", updated_data['data']['title'])
        
        # Add more fields
        print("\n🔄 Adding more fields...")
        await jd_data.update_field("company_name", "TechCorp")
        await jd_data.update_field("salary_range", "$120k-$150k")
        
        # Check again
        response = requests.get('http://localhost:7862/api/jd-data')
        if response.ok:
            final_data = response.json()
            print("✅ Final API state:")
            print(f"  Title: {final_data['data']['title']}")
            print(f"  Company: {final_data['data']['company']}")  
            print(f"  Salary: {final_data['data']['salaryRange']}")
            print(f"  Extracted Fields: {final_data['extractedFields']}")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        api_server.stop()
        print("\n🔄 Test completed")


if __name__ == "__main__":
    asyncio.run(test_api_updates())