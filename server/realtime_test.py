#!/usr/bin/env python3
"""
Real-time JD extraction simulation with slower updates for better visualization
"""

import asyncio
import time
from interview_extractor import JDData
from jd_api_server import JDAPIServer


async def realtime_demo():
    """Simulate real-time extraction with slower updates for demo."""
    print("🎬 Real-Time JD Extraction Demo")
    print("📡 Frontend should show live updates as they happen!")
    print()
    
    # Create fresh JD data and API server
    jd_data = JDData()
    api_server = JDAPIServer(jd_data, port=7861)
    
    try:
        # Start API server
        api_server.start()
        await asyncio.sleep(2)
        
        print("📡 API Server running on http://localhost:7861")
        print("📱 Open http://localhost:3000 to see live updates")
        print("⏰ Starting extraction in 5 seconds...")
        print()
        
        await asyncio.sleep(5)
        
        # Simulate voice extraction with realistic delays
        extractions = [
            ("job_title", "Senior Full-Stack Developer", "🏷️ Job title extracted"),
            ("company_name", "AI Innovations Corp", "🏢 Company name captured"),
            ("salary_range", "$130,000 - $170,000", "💰 Salary range detected"),
            ("work_arrangement", "Hybrid (2 days remote)", "🏠 Work arrangement identified"),
            ("employment_type", "Full-time", "⏰ Employment type confirmed"),
            ("required_qualifications", "Bachelor's in CS\n5+ years full-stack development\nReact and Node.js expertise", "📋 Required qualifications listed"),
            ("responsibilities", "Architect scalable web applications\nLead technical decision-making\nMentor development team\nCollaborate with product managers", "📝 Key responsibilities defined"),
            ("technical_skills", ["React", "Node.js", "TypeScript", "PostgreSQL", "AWS", "Docker"], "🛠️ Technical skills catalogued"),
        ]
        
        print("🎤 Starting voice extraction simulation...")
        print("👀 Watch the frontend for real-time updates!")
        print()
        
        for i, (field, value, description) in enumerate(extractions):
            # Wait between updates to show real-time effect
            await asyncio.sleep(8)  # 8 second delay for dramatic effect
            
            print(f"🗣️ User mentioned: {description}")
            await jd_data.update_field(field, value)
            print(f"✅ {field} → {value}")
            print(f"📊 Progress: {len(jd_data.get_collected_fields())}/{len(jd_data.get_all_fields())} fields complete")
            print("🌐 Frontend should update automatically now!")
            print("-" * 50)
            
        print()
        print("🎉 Real-time extraction demo complete!")
        print("📱 Frontend should show all fields filled with live animations")
        print("⏳ Keeping server alive for continued testing...")
        
        # Keep server running for manual testing
        await asyncio.sleep(300)  # 5 minutes
        
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo error: {e}")
    finally:
        api_server.stop()
        print("🔄 Demo completed")


if __name__ == "__main__":
    asyncio.run(realtime_demo())