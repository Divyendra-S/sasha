#!/usr/bin/env python3
"""
Clean API server for testing real voice integration
"""

import asyncio
from interview_extractor import JDData
from jd_api_server import JDAPIServer


async def clean_api_server():
    """Run a clean API server with empty JD data for real testing."""
    print("🧹 Starting Clean API Server")
    print("📡 API will serve empty JD data initially")
    print("🎤 Connect your voice bot to populate data")
    print()
    
    # Create fresh, empty JD data
    jd_data = JDData()
    api_server = JDAPIServer(jd_data, port=7861)
    
    try:
        # Start API server
        api_server.start()
        await asyncio.sleep(1)
        
        print("✅ Clean API Server running on http://localhost:7861")
        print("📱 Frontend at http://localhost:3000 should show empty form")
        print("🗣️ Now start your voice bot to see real-time extraction!")
        print("⏹️ Press Ctrl+C to stop")
        print()
        
        # Keep server running indefinitely
        while True:
            await asyncio.sleep(1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Stopping clean API server...")
    finally:
        api_server.stop()
        print("🔄 Clean API server stopped")


if __name__ == "__main__":
    asyncio.run(clean_api_server())