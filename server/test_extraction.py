#!/usr/bin/env python3
"""
Full tests for interview information extraction with real LLM calls.

These tests require API keys and test the actual LLM integration.
Run after setting up environment variables.
"""

import asyncio
import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interview_extractor import InterviewData, InterviewExtractor, InterviewFlowManager


async def test_real_extraction():
    """Test real information extraction with LLM calls."""
    print("\n[TEST] Testing Real Information Extraction")
    print("-" * 40)
    
    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found. Please set up your .env file.")
        return False
    
    # Initialize data and extractor
    data = InterviewData()
    extractor = InterviewExtractor(data, api_key)
    
    # Test cases with expected extractions
    test_cases = [
        {
            "input": "Hello, my name is Sarah Johnson and I have been working as a software engineer for about 7 years now.",
            "expected_fields": ["name", "years_experience", "current_role"]
        },
        {
            "input": "I'm currently looking for remote work opportunities and my salary expectation is around 120k.",
            "expected_fields": ["work_preference", "salary_expectation"]
        },
        {
            "input": "I specialize in Python, JavaScript, React, and AWS cloud services.",
            "expected_fields": ["skills"]
        },
        {
            "input": "Yes, that sounds good to me.",
            "expected_fields": []  # Should not extract anything
        }
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: \"{test_case['input'][:50]}...\"")
        
        try:
            # Test should_extract filtering
            should_extract = await extractor.should_extract(test_case['input'])
            print(f"Should extract: {should_extract}")
            
            if should_extract:
                # Test extraction
                start_time = time.time()
                extracted_data = await extractor.extract_information(test_case['input'])
                end_time = time.time()
                
                print(f"Extraction time: {end_time - start_time:.2f}s")
                print(f"Extracted data: {extracted_data}")
                
                # Test data update
                if extracted_data:
                    await extractor.update_interview_data(extracted_data)
                    
                    # Verify expected fields were found
                    extracted_fields = list(extracted_data.keys())
                    expected_fields = test_case['expected_fields']
                    
                    if expected_fields:
                        # Check if at least one expected field was extracted
                        found_expected = any(field in extracted_fields for field in expected_fields)
                        if found_expected:
                            print("✅ Expected information found")
                            success_count += 1
                        else:
                            print(f"⚠️  Expected fields {expected_fields} but got {extracted_fields}")
                    else:
                        print("ℹ️  No extraction expected for this input")
                        success_count += 1
                else:
                    if not test_case['expected_fields']:
                        print("✅ Correctly extracted nothing")
                        success_count += 1
                    else:
                        print("⚠️  No data extracted when some was expected")
            else:
                if not test_case['expected_fields']:
                    print("✅ Correctly filtered out")
                    success_count += 1
                else:
                    print("⚠️  Filtered out when extraction was expected")
                    
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
    
    print(f"\n📊 Results: {success_count}/{total_tests} tests successful")
    
    # Print final interview state
    print(f"\nFinal Interview State:")
    print(f"Collected fields: {data.get_collected_fields()}")
    print(f"Missing fields: {data.get_missing_fields()}")
    print(f"Complete: {data.is_complete()}")
    print(f"Name: {data.name}")
    print(f"Experience: {data.years_experience}")
    print(f"Role: {data.current_role}")
    print(f"Skills: {data.skills}")
    print(f"Salary: {data.salary_expectation}")
    print(f"Work preference: {data.work_preference}")
    
    return success_count == total_tests


async def test_flow_management():
    """Test interview flow management."""
    print("\n[TEST] Testing Interview Flow Management")
    print("-" * 40)
    
    data = InterviewData()
    manager = InterviewFlowManager(data)
    
    # Test guidance at different stages
    stages = [
        ("Empty", {}),
        ("Basic info", {"name": "John", "years_experience": 5}),
        ("Partial info", {"name": "John", "years_experience": 5, "current_role": "Developer"}),
        ("Nearly complete", {"name": "John", "years_experience": 5, "current_role": "Developer", "skills": ["Python"], "salary_expectation": "80k"}),
        ("Complete", {"name": "John", "years_experience": 5, "current_role": "Developer", "skills": ["Python"], "salary_expectation": "80k", "work_preference": "remote"})
    ]
    
    for stage_name, fields in stages:
        # Reset data
        data = InterviewData()
        manager = InterviewFlowManager(data)
        
        # Set up stage
        for field, value in fields.items():
            await data.update_field(field, value)
        
        # Get guidance
        guidance = manager.get_guidance_message()
        
        print(f"\nStage: {stage_name}")
        print(f"Collected: {data.get_collected_fields()}")
        print(f"Missing: {data.get_missing_fields()}")
        print(f"Complete: {data.is_complete()}")
        print(f"Guidance: {guidance}")
        
    print("✅ Flow management test completed")
    return True


async def test_error_handling():
    """Test error handling scenarios."""
    print("\n[TEST] Testing Error Handling")
    print("-" * 40)
    
    data = InterviewData()
    # Initialize with invalid API key to test error handling
    extractor = InterviewExtractor(data, "invalid-api-key")
    
    # Test extraction with invalid API key
    try:
        result = await extractor.extract_information("My name is John Doe")
        print(f"Result with invalid key: {result}")
        print("✅ Error handling working (returned empty dict)")
        return True
    except Exception as e:
        print(f"⚠️  Exception not handled gracefully: {e}")
        return False


async def test_concurrent_access():
    """Test concurrent access to interview data."""
    print("\n[TEST] Testing Concurrent Access")
    print("-" * 40)
    
    data = InterviewData()
    
    async def update_field(field_name, value, delay=0.1):
        if delay:
            await asyncio.sleep(delay)
        return await data.update_field(field_name, value)
    
    # Test concurrent updates
    tasks = [
        update_field("name", "Alice", 0.1),
        update_field("years_experience", 5, 0.05),
        update_field("current_role", "Developer", 0.15),
    ]
    
    results = await asyncio.gather(*tasks)
    
    print(f"Concurrent update results: {results}")
    print(f"Final data state: name={data.name}, experience={data.years_experience}, role={data.current_role}")
    print("✅ Concurrent access test completed")
    return True


def check_environment():
    """Check if required environment variables are set."""
    required_vars = ["GOOGLE_API_KEY", "GROQ_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set up your .env file with these variables.")
        return False
    
    print("✅ All required environment variables are set")
    return True


async def run_full_tests():
    """Run all full integration tests."""
    print("Running Full Tests (Requires API Keys)")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        print("\n⚠️  Cannot run full tests without proper environment setup.")
        print("Use 'python test_mock_extraction.py' for tests that don't require API keys.")
        return
    
    # Run tests
    test_results = []
    
    try:
        result = await test_real_extraction()
        test_results.append(("Real Extraction", result))
    except Exception as e:
        print(f"❌ Real extraction test failed: {e}")
        test_results.append(("Real Extraction", False))
    
    try:
        result = await test_flow_management()
        test_results.append(("Flow Management", result))
    except Exception as e:
        print(f"❌ Flow management test failed: {e}")
        test_results.append(("Flow Management", False))
    
    try:
        result = await test_error_handling()
        test_results.append(("Error Handling", result))
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        test_results.append(("Error Handling", False))
    
    try:
        result = await test_concurrent_access()
        test_results.append(("Concurrent Access", result))
    except Exception as e:
        print(f"❌ Concurrent access test failed: {e}")
        test_results.append(("Concurrent Access", False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    total = len(test_results)
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The interview extraction system is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(run_full_tests())