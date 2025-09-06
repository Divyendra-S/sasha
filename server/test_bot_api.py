#!/usr/bin/env python3
"""
Test the bot with API server and simulate extraction
"""

import asyncio
import time
from interview_extractor import JDData, JDExtractor
from jd_api_server import JDAPIServer


async def simulate_extraction():
    """Simulate the extraction that would happen during a voice session."""
    print("🎤 Simulating voice bot extraction...")
    
    # Create the same setup as in bot.py
    jd_data = JDData()
    api_server = JDAPIServer(jd_data, port=7861)  # Same port as bot
    
    try:
        # Start API server
        api_server.start()
        await asyncio.sleep(2)  # Let it start
        
        print("📡 API Server running on http://localhost:7861")
        print("📡 You can test: curl http://localhost:7861/api/jd-data")
        print("📡 Frontend should be able to poll this endpoint")
        print()
        
        # Simulate gradual extraction like the voice bot would do
        extractions = [
            ("job_title", "Senior React Developer"),
            ("company_name", "TechStartup Inc"),
            ("salary_range", "$120,000 - $150,000"),
            ("work_arrangement", "Remote-friendly"),
            ("employment_type", "Full-time"),
            ("required_qualifications", "5+ years React experience\nTypeScript proficiency"),
            ("responsibilities", "Lead frontend development\nMentor junior developers\nArchitect scalable solutions"),
            ("technical_skills", ["React", "TypeScript", "Node.js", "GraphQL"]),
        ]
        
        print("🔄 Starting gradual data extraction simulation...")
        for i, (field, value) in enumerate(extractions):
            await asyncio.sleep(3)  # 3 second delay between updates
            await jd_data.update_field(field, value)
            print(f"✅ Step {i+1}/{len(extractions)}: Updated {field}")
            print(f"📊 Progress: {len(jd_data.get_collected_fields())}/{len(jd_data.get_all_fields())} fields")
            print("🌐 API should now reflect this update for frontend polling")
            print()
        
        print("🎉 All simulated extractions complete!")
        print("📡 API server will keep running - test with frontend now")
        print("⏰ Keeping server alive for 60 seconds...")
        
        # Keep the server running for testing
        await asyncio.sleep(60)
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    finally:
        api_server.stop()
        print("🔄 API server stopped")


if __name__ == "__main__":
    print("🧪 Bot API Integration Test")
    print("📝 This simulates what happens during a real voice session")
    print("📡 Test the frontend polling at: http://localhost:3000")
    print()
    
    asyncio.run(simulate_extraction())