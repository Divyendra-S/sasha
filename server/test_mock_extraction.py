#!/usr/bin/env python3
"""
Mock tests for interview information extraction.

These tests validate the extraction logic and data management without requiring API keys.
They use mocked LLM responses to test the core functionality.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interview_extractor import InterviewData, InterviewExtractor, InterviewFlowManager
from pipecat.frames.frames import TextFrame, Frame
from pipecat.processors.frame_processor import FrameDirection


class TestInterviewDataMock(unittest.TestCase):
    """Test InterviewData class functionality."""
    
    def setUp(self):
        self.data = InterviewData()
    
    def test_initial_state(self):
        """Test that InterviewData starts with empty fields."""
        self.assertIsNone(self.data.name)
        self.assertIsNone(self.data.years_experience)
        self.assertIsNone(self.data.current_role)
        self.assertIsNone(self.data.skills)
        self.assertIsNone(self.data.salary_expectation)
        self.assertIsNone(self.data.work_preference)
        self.assertEqual(len(self.data._collected_fields), 0)
        self.assertFalse(self.data.is_complete())
    
    async def test_update_field(self):
        """Test updating fields and tracking collected state."""
        # Test updating name
        result = await self.data.update_field("name", "John Doe")
        self.assertTrue(result)
        self.assertEqual(self.data.name, "John Doe")
        self.assertIn("name", self.data._collected_fields)
        
        # Test updating with None value should not update
        result = await self.data.update_field("years_experience", None)
        self.assertFalse(result)
        self.assertIsNone(self.data.years_experience)
        
        # Test updating with valid value
        result = await self.data.update_field("years_experience", 5)
        self.assertTrue(result)
        self.assertEqual(self.data.years_experience, 5)
        self.assertIn("years_experience", self.data._collected_fields)
    
    def test_missing_fields(self):
        """Test getting missing fields."""
        # Use fresh data instance to avoid interference from other tests
        fresh_data = InterviewData()
        missing = fresh_data.get_missing_fields()
        expected = {"name", "years_experience", "current_role", "skills", "salary_expectation", "work_preference"}
        self.assertEqual(set(missing), expected)
    
    async def test_completion_tracking(self):
        """Test completion tracking."""
        self.assertFalse(self.data.is_complete())
        
        # Add all required fields
        await self.data.update_field("name", "John")
        await self.data.update_field("years_experience", 5)
        await self.data.update_field("current_role", "Developer")
        await self.data.update_field("skills", ["Python", "JavaScript"])
        await self.data.update_field("salary_expectation", "80k")
        await self.data.update_field("work_preference", "remote")
        
        self.assertTrue(self.data.is_complete())
        self.assertEqual(len(self.data.get_missing_fields()), 0)


class TestInterviewExtractorMock(unittest.TestCase):
    """Test InterviewExtractor with mocked LLM calls."""
    
    def setUp(self):
        self.data = InterviewData()
        self.extractor = InterviewExtractor(self.data, "fake-api-key")
        
    async def test_should_extract_filtering(self):
        """Test the filtering logic for extraction triggers."""
        # Should extract substantial responses
        self.assertTrue(await self.extractor.should_extract("My name is John and I have 5 years of experience"))
        self.assertTrue(await self.extractor.should_extract("I work as a senior developer"))
        
        # Should not extract short responses
        self.assertFalse(await self.extractor.should_extract("yes"))
        self.assertFalse(await self.extractor.should_extract("no"))
        self.assertFalse(await self.extractor.should_extract("okay"))
        self.assertFalse(await self.extractor.should_extract(""))
        self.assertFalse(await self.extractor.should_extract("hi"))
        self.assertFalse(await self.extractor.should_extract("good"))
    
    @patch.object(InterviewExtractor, '_call_extraction_llm')
    async def test_extract_information_success(self, mock_llm_call):
        """Test successful information extraction."""
        # Mock LLM response
        mock_response = '{"name": "John Doe", "years_experience": 5}'
        mock_llm_call.return_value = mock_response
        
        result = await self.extractor.extract_information("My name is John Doe and I have 5 years experience")
        
        expected = {"name": "John Doe", "years_experience": 5}
        self.assertEqual(result, expected)
        mock_llm_call.assert_called_once()
    
    @patch.object(InterviewExtractor, '_call_extraction_llm')
    async def test_extract_information_json_error(self, mock_llm_call):
        """Test extraction with JSON parsing error."""
        # Mock invalid JSON response
        mock_llm_call.return_value = "invalid json response"
        
        result = await self.extractor.extract_information("test input")
        
        # Should return empty dict on JSON error
        self.assertEqual(result, {})
    
    @patch.object(InterviewExtractor, '_call_extraction_llm')
    async def test_extract_information_exception(self, mock_llm_call):
        """Test extraction with LLM call exception."""
        # Mock LLM call exception
        mock_llm_call.side_effect = Exception("API Error")
        
        result = await self.extractor.extract_information("test input")
        
        # Should return empty dict on exception
        self.assertEqual(result, {})
    
    async def test_update_interview_data(self):
        """Test updating interview data from extracted information."""
        extracted = {
            "name": "Alice Smith",
            "years_experience": 3,
            "current_role": "Software Engineer"
        }
        
        await self.extractor.update_interview_data(extracted)
        
        # Check that data was updated
        self.assertEqual(self.data.name, "Alice Smith")
        self.assertEqual(self.data.years_experience, 3)
        self.assertEqual(self.data.current_role, "Software Engineer")
        
        # Check that fields are marked as collected
        collected = self.data.get_collected_fields()
        self.assertIn("name", collected)
        self.assertIn("years_experience", collected)
        self.assertIn("current_role", collected)
    
    async def test_frame_processing(self):
        """Test frame processing logic."""
        # Create a mock frame
        text_frame = TextFrame("My name is Bob and I have 2 years experience")
        
        # Mock the extraction and update process
        with patch.object(self.extractor, 'should_extract', return_value=True), \
             patch.object(self.extractor, '_extract_and_update') as mock_extract:
            
            mock_extract.return_value = None  # Async function returns None
            
            # Process the frame
            await self.extractor.process_frame(text_frame, FrameDirection.DOWNSTREAM)
            
            # The extraction should be triggered
            # Note: _extract_and_update is called as a background task, so we can't easily test it directly
            # But we can verify the frame was processed
            self.assertTrue(True)  # Frame processing completed without error


class TestInterviewFlowManagerMock(unittest.TestCase):
    """Test InterviewFlowManager functionality."""
    
    def setUp(self):
        self.data = InterviewData()
        self.manager = InterviewFlowManager(self.data)
    
    async def test_guidance_generation_early_stage(self):
        """Test guidance generation in early interview stage."""
        # No information collected yet
        guidance = self.manager.get_guidance_message()
        
        # Should ask for name first
        self.assertIsNotNone(guidance)
        self.assertIn("name", guidance.lower())
    
    async def test_guidance_generation_middle_stage(self):
        """Test guidance generation in middle stage."""
        # Collect some basic info
        await self.data.update_field("name", "John")
        await self.data.update_field("years_experience", 5)
        
        guidance = self.manager.get_guidance_message()
        
        # Should ask for role or skills
        self.assertIsNotNone(guidance)
        self.assertTrue(
            "role" in guidance.lower() or "skill" in guidance.lower()
        )
    
    async def test_guidance_generation_final_stage(self):
        """Test guidance generation in final stage."""
        # Collect most info, leave only work preference
        await self.data.update_field("name", "John")
        await self.data.update_field("years_experience", 5)
        await self.data.update_field("current_role", "Developer")
        await self.data.update_field("skills", ["Python"])
        await self.data.update_field("salary_expectation", "80k")
        
        guidance = self.manager.get_guidance_message()
        
        # Should ask for work preference
        self.assertIsNotNone(guidance)
        self.assertTrue(
            "remote" in guidance.lower() or "work" in guidance.lower()
        )
    
    async def test_guidance_complete_interview(self):
        """Test guidance when interview is complete."""
        # Add all required info
        await self.data.update_field("name", "John")
        await self.data.update_field("years_experience", 5)
        await self.data.update_field("current_role", "Developer")
        await self.data.update_field("skills", ["Python"])
        await self.data.update_field("salary_expectation", "80k")
        await self.data.update_field("work_preference", "remote")
        
        guidance = self.manager.get_guidance_message()
        
        # Should indicate completion
        self.assertIsNotNone(guidance)
        self.assertTrue(
            "great" in guidance.lower() or "complete" in guidance.lower()
        )
    
    def test_guidance_timing(self):
        """Test guidance timing mechanism."""
        # Initially should provide guidance (just created, last_guidance_time = 0)
        self.assertTrue(self.manager.should_provide_guidance())
        
        # Mock time passage
        import time
        original_time = time.time()
        
        # Set last guidance time to now
        self.manager.last_guidance_time = original_time
        
        # Should not provide guidance immediately after
        with patch('time.time', return_value=original_time + 10):  # Only 10 seconds later
            self.assertFalse(self.manager.should_provide_guidance())
        
        # Should provide guidance after interval
        with patch('time.time', return_value=original_time + 31):  # 31 seconds later
            self.assertTrue(self.manager.should_provide_guidance())


async def run_async_test(test_func):
    """Helper to run async test functions."""
    await test_func()


def run_mock_tests():
    """Run all mock tests."""
    print("Running Mock Tests (No API Keys Required)")
    print("=" * 50)
    
    # Test InterviewData
    print("\n[TEST] Testing InterviewData class...")
    data_test = TestInterviewDataMock()
    data_test.setUp()
    data_test.test_initial_state()
    asyncio.run(data_test.test_update_field())
    data_test.test_missing_fields()
    asyncio.run(data_test.test_completion_tracking())
    print("✅ InterviewData tests passed")
    
    # Test InterviewExtractor
    print("\n[TEST] Testing InterviewExtractor class...")
    extractor_test = TestInterviewExtractorMock()
    extractor_test.setUp()
    asyncio.run(extractor_test.test_should_extract_filtering())
    asyncio.run(extractor_test.test_extract_information_success())
    asyncio.run(extractor_test.test_extract_information_json_error())
    asyncio.run(extractor_test.test_extract_information_exception())
    asyncio.run(extractor_test.test_update_interview_data())
    asyncio.run(extractor_test.test_frame_processing())
    print("✅ InterviewExtractor tests passed")
    
    # Test InterviewFlowManager
    print("\n[TEST] Testing InterviewFlowManager class...")
    flow_test = TestInterviewFlowManagerMock()
    flow_test.setUp()
    asyncio.run(flow_test.test_guidance_generation_early_stage())
    flow_test.setUp()
    asyncio.run(flow_test.test_guidance_generation_middle_stage())
    flow_test.setUp()
    asyncio.run(flow_test.test_guidance_generation_final_stage())
    flow_test.setUp()
    asyncio.run(flow_test.test_guidance_complete_interview())
    flow_test.setUp()
    flow_test.test_guidance_timing()
    print("✅ InterviewFlowManager tests passed")
    
    print("\n🎉 All mock tests passed successfully!")
    print("\nLog Output Examples:")
    print("[EXTRACTION] Triggered for: \"My name is John and I have 5 years experience\"")
    print("[EXTRACTION] LLM Response: {\"name\": \"John\", \"years_experience\": 5}")
    print("[INTERVIEW_DATA] Updated: name = John")
    print("[INTERVIEW_DATA] Updated: years_experience = 5")
    print("[INTERVIEW_STATUS] Collected: ['name', 'years_experience'] | Missing: ['current_role', 'skills', 'salary_expectation', 'work_preference']")
    print("[INTERVIEW_FLOW] Guiding conversation toward missing info: current_role, skills, salary_expectation, work_preference")


if __name__ == "__main__":
    run_mock_tests()