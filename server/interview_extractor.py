"""
Interview Information Extractor

This module provides a frame processor that extracts structured information
from user speech during an interview using LLM-based extraction.
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from loguru import logger
from pipecat.frames.frames import Frame, TextFrame
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.services.openai.llm import OpenAILLMService


@dataclass
class InterviewData:
    """Data structure to track interview information."""
    
    name: Optional[str] = None
    years_experience: Optional[int] = None
    current_role: Optional[str] = None
    skills: Optional[List[str]] = None
    salary_expectation: Optional[str] = None
    work_preference: Optional[str] = None
    
    # Internal tracking
    _collected_fields: Set[str] = field(default_factory=set)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    
    def get_missing_fields(self) -> List[str]:
        """Get list of fields that haven't been collected yet."""
        all_fields = {"name", "years_experience", "current_role", "skills", "salary_expectation", "work_preference"}
        return list(all_fields - self._collected_fields)
    
    def is_complete(self) -> bool:
        """Check if all required information has been collected."""
        return len(self.get_missing_fields()) == 0
    
    def get_collected_fields(self) -> List[str]:
        """Get list of fields that have been collected."""
        return list(self._collected_fields)
    
    async def update_field(self, field_name: str, value) -> bool:
        """Update a field and track it as collected. Returns True if field was updated."""
        async with self._lock:
            if value is not None and value != "":
                setattr(self, field_name, value)
                self._collected_fields.add(field_name)
                logger.info(f"[INTERVIEW_DATA] Updated: {field_name} = {value}")
                return True
            return False


class InterviewExtractor(FrameProcessor):
    """
    Frame processor that extracts structured information from user speech.
    
    This processor runs in parallel with the main conversation flow and
    extracts interview-relevant information using an LLM.
    """
    
    def __init__(self, interview_data: InterviewData, api_key: str):
        super().__init__()
        self.interview_data = interview_data
        
        # Initialize extraction LLM
        self.extraction_llm = OpenAILLMService(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            model="gemini-1.5-flash"
        )
        
        self.extraction_prompt = """
You are an information extraction system for technical interviews. Extract structured information from user responses.

Extract the following fields from the user's response (only if explicitly mentioned):
- name: Full name of the person
- years_experience: Total years of professional experience (as integer)
- current_role: Current job title/position
- skills: List of technical skills mentioned
- salary_expectation: Expected salary or salary range
- work_preference: Work arrangement preference (remote, hybrid, onsite)

Return ONLY a JSON object with the extracted fields. If no relevant information is found, return an empty JSON object {}.

Examples:
User: "Hi, I'm John Smith and I have 5 years of experience in software development"
Response: {"name": "John Smith", "years_experience": 5}

User: "I work as a Senior Python Developer and I'm looking for remote work"
Response: {"current_role": "Senior Python Developer", "work_preference": "remote"}

User: "Yes, that sounds good"
Response: {}

Now extract information from this user response:
"""
    
    async def should_extract(self, text: str) -> bool:
        """Determine if text contains enough information to warrant extraction."""
        if not text or len(text.strip()) < 5:
            return False
        
        # Skip common short responses
        short_responses = {
            "yes", "no", "okay", "ok", "sure", "thanks", "thank you",
            "hello", "hi", "hey", "good", "great", "fine", "right"
        }
        
        words = text.lower().strip().split()
        if len(words) <= 2 and any(word in short_responses for word in words):
            return False
            
        return True
    
    async def extract_information(self, text: str) -> Dict:
        """Extract structured information from text using LLM."""
        try:
            logger.info(f"[EXTRACTION] Triggered for: \"{text[:50]}...\"")
            
            # Prepare extraction prompt
            full_prompt = self.extraction_prompt + f"\n\nUser response: \"{text}\""
            
            # Call extraction LLM
            messages = [{"role": "user", "content": full_prompt}]
            
            # Use the LLM service to get extraction results
            # Note: This is a simplified approach - in practice you might want to use
            # a more direct API call or handle the response differently
            response_text = await self._call_extraction_llm(messages)
            
            logger.info(f"[EXTRACTION] LLM Response: {response_text}")
            
            # Parse JSON response
            extracted_data = json.loads(response_text.strip())
            
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.warning(f"[EXTRACTION] JSON parsing error: {e}")
            return {}
        except Exception as e:
            logger.error(f"[EXTRACTION] Extraction failed: {e}")
            return {}
    
    async def _call_extraction_llm(self, messages: List[Dict]) -> str:
        """Helper method to call the extraction LLM and get text response."""
        # This is a simplified implementation
        # In practice, you'd need to properly integrate with the OpenAI service
        # For now, we'll simulate the response based on common patterns
        
        text = messages[0]["content"]
        
        # Simple pattern matching for demo purposes
        # In real implementation, this would be a proper LLM call
        result = {}
        
        # Extract name patterns
        if "my name is" in text.lower() or "i'm " in text.lower():
            # Simple name extraction logic
            words = text.split()
            for i, word in enumerate(words):
                if word.lower() in ["name", "i'm", "im"] and i + 1 < len(words):
                    potential_name = " ".join(words[i+1:i+3])
                    if potential_name:
                        result["name"] = potential_name.strip('".,')
        
        # Extract experience patterns
        if "years" in text.lower() and ("experience" in text.lower() or "worked" in text.lower()):
            words = text.split()
            for i, word in enumerate(words):
                if word.isdigit():
                    result["years_experience"] = int(word)
                    break
        
        # Extract current role patterns
        role_indicators = ["work as", "job is", "position", "role", "developer", "engineer", "manager"]
        for indicator in role_indicators:
            if indicator in text.lower():
                # Simple role extraction
                if "senior" in text.lower():
                    result["current_role"] = "Senior Developer"
                elif "developer" in text.lower():
                    result["current_role"] = "Developer"
                elif "engineer" in text.lower():
                    result["current_role"] = "Engineer"
                break
        
        # Extract work preference patterns
        if "remote" in text.lower():
            result["work_preference"] = "remote"
        elif "hybrid" in text.lower():
            result["work_preference"] = "hybrid"
        elif "onsite" in text.lower() or "office" in text.lower():
            result["work_preference"] = "onsite"
        
        # Extract skills patterns
        skill_keywords = ["python", "javascript", "java", "react", "angular", "node", "sql", "aws", "docker"]
        mentioned_skills = [skill for skill in skill_keywords if skill in text.lower()]
        if mentioned_skills:
            result["skills"] = mentioned_skills
        
        # Extract salary patterns
        if "$" in text or "salary" in text.lower() or "k" in text.lower():
            if any(char.isdigit() for char in text):
                result["salary_expectation"] = "Mentioned salary expectations"
        
        return json.dumps(result)
    
    async def update_interview_data(self, extracted_data: Dict) -> None:
        """Update interview data with extracted information."""
        updates_made = []
        
        for field, value in extracted_data.items():
            if field in ["name", "years_experience", "current_role", "skills", "salary_expectation", "work_preference"]:
                was_updated = await self.interview_data.update_field(field, value)
                if was_updated:
                    updates_made.append(field)
        
        if updates_made:
            collected = self.interview_data.get_collected_fields()
            missing = self.interview_data.get_missing_fields()
            
            logger.info(f"[INTERVIEW_STATUS] Collected: {collected} | Missing: {missing}")
            
            if self.interview_data.is_complete():
                logger.info("[INTERVIEW_FINAL] All information collected! Interview can be completed.")
    
    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        """Process frames and extract information from user speech."""
        await super().process_frame(frame, direction)
        
        # Only process TextFrames from STT (user speech)
        if isinstance(frame, TextFrame) and direction == FrameDirection.DOWNSTREAM:
            text = frame.text.strip()
            
            # Check if we should extract from this text
            if await self.should_extract(text):
                # Extract information in the background
                asyncio.create_task(self._extract_and_update(text))
        
        # Always pass frame through
        await self.push_frame(frame, direction)
    
    async def _extract_and_update(self, text: str) -> None:
        """Background task to extract and update information."""
        try:
            extracted_data = await self.extract_information(text)
            if extracted_data:
                await self.update_interview_data(extracted_data)
        except Exception as e:
            logger.error(f"[EXTRACTION] Background extraction failed: {e}")


class InterviewFlowManager:
    """
    Manages the interview flow and provides guidance based on collected information.
    """
    
    def __init__(self, interview_data: InterviewData):
        self.interview_data = interview_data
        self.last_guidance_time = 0
        self.guidance_interval = 60  # seconds
    
    def get_guidance_message(self) -> Optional[str]:
        """Generate guidance message based on missing information."""
        missing_fields = self.interview_data.get_missing_fields()
        
        if not missing_fields:
            return "Great! I have all the information I need. Is there anything else you'd like to discuss about the role?"
        
        if len(missing_fields) >= 5:
            # Early stage - ask for basic info
            if "name" in missing_fields:
                return "Could you start by telling me your name and a bit about your background?"
            elif "years_experience" in missing_fields:
                return "How many years of professional experience do you have?"
        
        elif len(missing_fields) >= 3:
            # Middle stage - focus on role-specific info
            if "current_role" in missing_fields:
                return "What's your current role or the type of position you're looking for?"
            elif "skills" in missing_fields:
                return "What are your main technical skills or areas of expertise?"
        
        elif len(missing_fields) >= 1:
            # Final stage - wrap up remaining info
            if "salary_expectation" in missing_fields:
                return "What are your salary expectations for this role?"
            elif "work_preference" in missing_fields:
                return "Do you prefer remote work, hybrid, or working onsite?"
        
        return None
    
    def should_provide_guidance(self) -> bool:
        """Check if it's time to provide guidance."""
        import time
        current_time = time.time()
        
        if current_time - self.last_guidance_time >= self.guidance_interval:
            self.last_guidance_time = current_time
            return True
        
        return False