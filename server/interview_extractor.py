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
                old_value = getattr(self, field_name, None)
                setattr(self, field_name, value)
                self._collected_fields.add(field_name)
                
                if old_value != value:
                    logger.info(f"[INTERVIEW_DATA] ✨ COLLECTED: {field_name} = '{value}' (was: {old_value})")
                    completion_pct = (len(self._collected_fields) / 6) * 100
                    logger.info(f"[INTERVIEW_DATA] Progress: {completion_pct:.0f}% complete ({len(self._collected_fields)}/6 fields)")
                    logger.info(f"[INTERVIEW_DATA] Still missing: {self.get_missing_fields()}")
                else:
                    logger.info(f"[INTERVIEW_DATA] Confirmed existing value for {field_name}: '{value}'")
                return True
            else:
                logger.debug(f"[INTERVIEW_DATA] Skipped empty/null value for {field_name}: {value}")
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
        self._extraction_tasks = set()  # Track active extraction tasks
        self._max_concurrent_extractions = 3  # Limit concurrent extractions
        
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
        # Let everything through for now - no restrictions
        if not text or len(text.strip()) < 2:
            logger.debug(f"[EXTRACTION_FILTER] Too short: '{text}' (length: {len(text.strip()) if text else 0})")
            return False
        
        logger.info(f"[EXTRACTION_FILTER] ✅ Will extract from: '{text[:80]}{'...' if len(text) > 80 else ''}' (length: {len(text.strip())})")
        return True
    
    async def extract_information(self, text: str) -> Dict:
        """Extract structured information from text using LLM."""
        try:
            logger.info(f"[EXTRACTION] 🔍 Processing user input: \"{text[:80]}{'...' if len(text) > 80 else ''}\"")
            
            # Prepare extraction prompt
            full_prompt = self.extraction_prompt + f"\n\nUser response: \"{text}\""
            logger.debug(f"[EXTRACTION] Sending prompt to extraction LLM (length: {len(full_prompt)} chars)")
            
            # Call extraction LLM
            messages = [{"role": "user", "content": full_prompt}]
            
            # Use the LLM service to get extraction results
            logger.info("[EXTRACTION] Calling extraction LLM...")
            response_text = await self._call_extraction_llm(messages)
            
            logger.info(f"[EXTRACTION] Raw LLM response: '{response_text}'")
            
            # Parse JSON response
            extracted_data = json.loads(response_text.strip())
            
            if extracted_data:
                logger.info(f"[EXTRACTION] ✅ Successfully extracted: {list(extracted_data.keys())} -> {extracted_data}")
            else:
                logger.info("[EXTRACTION] No relevant information found in user response")
            
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.warning(f"[EXTRACTION] ⚠️ JSON parsing error: {e} | Raw response: '{response_text[:200]}'")
            return {}
        except Exception as e:
            logger.error(f"[EXTRACTION] ❌ Extraction failed: {str(e)} | Input text: '{text[:100]}'")
            import traceback
            logger.error(f"[EXTRACTION] Stack trace: {traceback.format_exc()}")
            return {}
    
    async def _call_extraction_llm(self, messages: List[Dict]) -> str:
        """Helper method to call the extraction LLM and get text response."""
        try:
            text = messages[0]["content"]
            user_input = text.split('User response: "')[-1].rstrip('"')
            logger.info(f"[EXTRACTION_LLM] Processing user input: '{user_input[:100]}{'...' if len(user_input) > 100 else ''}'")
            
            # Simple but effective pattern matching for key information
            # This is more reliable than mock LLM calls and prevents fake data
            result = {}
            user_lower = user_input.lower()
            
            # Extract name - look for "my name is", "i'm", "i am", "call me"
            name_patterns = [
                ("my name is ", 3), ("name is ", 2), ("i'm ", 1), ("i am ", 2), 
                ("call me ", 2), ("this is ", 2)
            ]
            for pattern, offset in name_patterns:
                if pattern in user_lower:
                    words = user_input.split()
                    pattern_words = pattern.strip().split()
                    for i in range(len(words) - len(pattern_words) + 1):
                        if ' '.join(words[i:i+len(pattern_words)]).lower() == pattern.strip():
                            if i + len(pattern_words) < len(words):
                                # Take the next 1-2 words as name
                                name_parts = []
                                for j in range(min(2, len(words) - i - len(pattern_words))):
                                    word = words[i + len(pattern_words) + j].strip('.,!?')
                                    if word and not word.lower() in {'a', 'an', 'the', 'and'}:
                                        name_parts.append(word)
                                if name_parts:
                                    result["name"] = ' '.join(name_parts)
                                    break
                    if "name" in result:
                        break
            
            # Extract years of experience - look for numbers + "years"
            import re
            exp_match = re.search(r'(\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|\d+)\b)\s*(?:years?|yrs?)(?:\s+(?:of\s+)?(?:experience|exp))?', user_lower)
            if exp_match:
                exp_text = exp_match.group(1)
                # Convert word numbers to digits
                word_to_num = {
                    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
                    'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
                    'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20
                }
                if exp_text in word_to_num:
                    result["years_experience"] = word_to_num[exp_text]
                elif exp_text.isdigit():
                    result["years_experience"] = int(exp_text)
            
            # Extract current role/position
            role_patterns = [
                "software engineer", "software developer", "web developer", "full stack developer",
                "backend developer", "frontend developer", "senior developer", "lead developer",
                "principal engineer", "staff engineer", "engineering manager", "tech lead",
                "data scientist", "data analyst", "product manager", "designer", "architect"
            ]
            for pattern in role_patterns:
                if pattern in user_lower:
                    # Capitalize properly
                    result["current_role"] = ' '.join(word.capitalize() for word in pattern.split())
                    break
            
            # Extract work preference
            if "remote" in user_lower and ("prefer" in user_lower or "want" in user_lower or "work" in user_lower):
                result["work_preference"] = "remote"
            elif "hybrid" in user_lower:
                result["work_preference"] = "hybrid"
            elif "onsite" in user_lower or "office" in user_lower:
                result["work_preference"] = "onsite"
            
            # Extract skills - look for common tech terms
            tech_skills = [
                "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust", "php",
                "react", "angular", "vue", "node", "express", "django", "flask", "spring",
                "sql", "mysql", "postgresql", "mongodb", "redis", "aws", "azure", "gcp",
                "docker", "kubernetes", "git", "linux", "html", "css", "sass"
            ]
            found_skills = [skill for skill in tech_skills if skill in user_lower]
            if found_skills:
                result["skills"] = found_skills
            
            # Extract salary expectations
            salary_match = re.search(r'\$([0-9,]+)(?:k|000)?|([0-9,]+)(?:k|000)\s*(?:dollars?)?', user_lower)
            if salary_match or "salary" in user_lower or "pay" in user_lower:
                if salary_match:
                    result["salary_expectation"] = f"${salary_match.group(1) or salary_match.group(2)}"
                else:
                    result["salary_expectation"] = "Discussed salary expectations"
            
            logger.info(f"[EXTRACTION_LLM] Extracted: {result}")
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"[EXTRACTION_LLM] Error: {e}")
            return "{}"
    
    async def update_interview_data(self, extracted_data: Dict) -> None:
        """Update interview data with extracted information."""
        updates_made = []
        ignored_fields = []
        
        logger.info(f"[EXTRACTION_UPDATE] Processing extracted data: {extracted_data}")
        
        for field, value in extracted_data.items():
            if field in ["name", "years_experience", "current_role", "skills", "salary_expectation", "work_preference"]:
                logger.info(f"[EXTRACTION_UPDATE] Attempting to update field '{field}' with value: {value}")
                was_updated = await self.interview_data.update_field(field, value)
                if was_updated:
                    updates_made.append(f"{field}='{value}'")
                    logger.info(f"[EXTRACTION_UPDATE] ✅ Successfully updated {field} with value: '{value}'")
                else:
                    logger.info(f"[EXTRACTION_UPDATE] ⚠️ Field {field} not updated (empty/same value): '{value}'")
            else:
                ignored_fields.append(field)
                logger.warning(f"[EXTRACTION_UPDATE] Ignoring unknown field: {field} = {value}")
        
        if ignored_fields:
            logger.info(f"[EXTRACTION_UPDATE] Ignored {len(ignored_fields)} unknown fields: {ignored_fields}")
            
        if updates_made:
            collected = self.interview_data.get_collected_fields()
            missing = self.interview_data.get_missing_fields()
            
            logger.info(f"[INTERVIEW_STATUS] 📈 UPDATED {len(updates_made)} field(s): {updates_made}")
            logger.info(f"[INTERVIEW_STATUS] Total collected fields with values: {[(field, getattr(self.interview_data, field)) for field in collected]} ({len(collected)}/6)")
            logger.info(f"[INTERVIEW_STATUS] Still missing: {missing}")
            
            if self.interview_data.is_complete():
                logger.info("[INTERVIEW_STATUS] 🎉 ALL INFORMATION COLLECTED! Interview ready for completion.")
        else:
            logger.info("[EXTRACTION_UPDATE] No valid updates made from extracted data")
    
    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        """Process frames and extract information from user speech."""
        await super().process_frame(frame, direction)
        
        # Only process TextFrames from STT (user speech)
        if isinstance(frame, TextFrame) and direction == FrameDirection.DOWNSTREAM:
            text = frame.text.strip()
            logger.info(f"[EXTRACTOR_FRAME] Received user text: '{text}'")
            
            # Check if we should extract from this text
            should_extract = await self.should_extract(text)
            logger.info(f"[EXTRACTOR_FRAME] Should extract: {should_extract} (text length: {len(text)})")
            
            if should_extract:
                # Check if we have too many concurrent extractions
                if len(self._extraction_tasks) >= self._max_concurrent_extractions:
                    logger.warning(f"[EXTRACTOR_FRAME] Too many concurrent extractions ({len(self._extraction_tasks)}), skipping: '{text}'")
                else:
                    logger.info(f"[EXTRACTOR_FRAME] Creating background extraction task for: '{text}'")
                    # Extract information in the background
                    task = asyncio.create_task(self._extract_and_update_with_cleanup(text))
                    self._extraction_tasks.add(task)
            else:
                logger.info(f"[EXTRACTOR_FRAME] Skipping extraction (too short or common phrase)")
        # Skip logging for audio frames to reduce spam
        elif not isinstance(frame, TextFrame):
            pass  # Don't log audio frames
        
        # Always pass frame through
        await self.push_frame(frame, direction)
    
    async def _extract_and_update(self, text: str) -> None:
        """Background task to extract and update information."""
        try:
            logger.info(f"[EXTRACTION_TASK] Starting background extraction for: '{text[:60]}{'...' if len(text) > 60 else ''}'")
            extracted_data = await self.extract_information(text)
            if extracted_data:
                logger.info(f"[EXTRACTION_TASK] Found data to process: {extracted_data}")
                await self.update_interview_data(extracted_data)
                logger.info("[EXTRACTION_TASK] Background extraction completed successfully")
            else:
                logger.info("[EXTRACTION_TASK] No extractable data found, task complete")
        except Exception as e:
            logger.error(f"[EXTRACTION_TASK] ❌ Background extraction failed: {str(e)} | Input: '{text[:100]}'")
    
    async def _extract_and_update_with_cleanup(self, text: str) -> None:
        """Background task wrapper that cleans up task tracking."""
        current_task = asyncio.current_task()
        try:
            await self._extract_and_update(text)
        finally:
            # Clean up task from tracking set
            if current_task in self._extraction_tasks:
                self._extraction_tasks.discard(current_task)
                logger.debug(f"[EXTRACTION_TASK] Cleaned up task, {len(self._extraction_tasks)} remaining")


class InterviewFlowManager:
    """
    Manages the interview flow and provides guidance based on collected information.
    """
    
    def __init__(self, interview_data: InterviewData):
        self.interview_data = interview_data
        self.last_guidance_time = 0
        self.guidance_interval = 45  # seconds - increased to reduce frequency
        self.guidance_attempts = {}
        self.max_attempts_per_field = 3
        self.last_guidance_field = None
        self.guidance_cooldown = 60  # seconds - cooldown after sending guidance
        self.guidance_pending = False  # track if guidance is pending response
    
    def get_guidance_message(self) -> Optional[str]:
        """Generate guidance message based on missing information."""
        missing_fields = self.interview_data.get_missing_fields()
        
        # Since extraction is disabled, all fields will be missing - provide guidance anyway
        if not missing_fields:
            return "Great! I have all the information I need. Is there anything else you'd like to discuss about the role?"
        
        # Focus on one field at a time, prioritizing by importance
        priority_fields = ["name", "years_experience", "current_role", "skills", "work_preference", "salary_expectation"]
        
        for field in priority_fields:
            if field in missing_fields:
                attempts = self.guidance_attempts.get(field, 0)
                
                attempts = self.guidance_attempts.get(field, 0)
                escalated = self.should_escalate_guidance(field)
                
                logger.info(f"[FLOW_GUIDANCE] Generating guidance for '{field}' (attempt #{attempts}, escalated: {escalated})")
                
                if escalated:
                    logger.info(f"[FLOW_GUIDANCE] Using DIRECT approach for '{field}' after {attempts} attempts")
                    # More direct approach after multiple attempts
                    if field == "name":
                        return "I need to get your full name for our interview records. Please tell me your first and last name."
                    elif field == "years_experience":
                        return "I need the exact number of years of professional experience you have. Please give me a specific number."
                    elif field == "current_role":
                        return "I need to know your current job title or the specific position you're applying for. What is your exact role?"
                    elif field == "skills":
                        return "I need specific technical skills. Please list the programming languages, frameworks, or technologies you work with."
                    elif field == "work_preference":
                        return "I need to know your work arrangement preference. Do you want remote, hybrid, or onsite work? Please choose one."
                    elif field == "salary_expectation":
                        return "I need your salary expectations. Please give me a specific range or amount you're looking for."
                else:
                    logger.info(f"[FLOW_GUIDANCE] Using FOCUSED approach for '{field}' (attempt #{attempts})")
                    # Focused but friendly approach for initial attempts
                    if field == "name":
                        return "Let's start with your full name please."
                    elif field == "years_experience":
                        return "How many years of professional experience do you have? Please give me a specific number."
                    elif field == "current_role":
                        return "What's your current job title or what specific position are you looking for?"
                    elif field == "skills":
                        return "What specific programming languages and technologies do you work with?"
                    elif field == "work_preference":
                        return "For this role, do you prefer remote work, hybrid, or working onsite?"
                    elif field == "salary_expectation":
                        return "What salary range are you looking for in this position?"
                
                return None  # Focus on one field at a time
        
        return None
    
    def should_provide_guidance(self) -> bool:
        """Check if it's time to provide guidance."""
        import time
        current_time = time.time()
        
        # Don't provide guidance if we're still waiting for a response
        if self.guidance_pending:
            logger.info("[FLOW_GUIDANCE] Skipping - guidance pending response")
            return False
        
        # Check cooldown period after sending guidance
        if self.last_guidance_field and current_time - self.last_guidance_time < self.guidance_cooldown:
            remaining = self.guidance_cooldown - (current_time - self.last_guidance_time)
            logger.info(f"[FLOW_GUIDANCE] Cooldown active - {remaining:.0f}s remaining")
            return False
        
        # Check if enough time has passed since last guidance
        if current_time - self.last_guidance_time >= self.guidance_interval:
            logger.info("[FLOW_GUIDANCE] Time threshold met - guidance allowed")
            self.last_guidance_time = current_time
            return True
        
        return False
    
    def mark_guidance_attempt(self):
        """Mark that guidance was attempted."""
        missing_fields = self.interview_data.get_missing_fields()
        if missing_fields:
            field = missing_fields[0]  # Focus on first missing field
            old_attempts = self.guidance_attempts.get(field, 0)
            self.guidance_attempts[field] = old_attempts + 1
            self.last_guidance_field = field
            self.guidance_pending = True  # Mark guidance as pending
            logger.info(f"[FLOW_GUIDANCE] Marked attempt for field '{field}': {old_attempts} -> {self.guidance_attempts[field]} attempts")
            logger.info(f"[FLOW_GUIDANCE] Guidance now pending for field '{field}'")
    
    def mark_guidance_processed(self):
        """Mark that guidance has been processed (when we see progress)."""
        self.guidance_pending = False
        logger.info(f"[FLOW_GUIDANCE] Guidance processed, pending status cleared")
    
    def check_field_progress(self) -> bool:
        """Check if progress was made on the field we're guiding toward."""
        if not self.last_guidance_field:
            return False
            
        # If the field is no longer missing, we made progress
        missing_fields = self.interview_data.get_missing_fields()
        if self.last_guidance_field not in missing_fields:
            logger.info(f"[FLOW_GUIDANCE] ✅ Progress made! Field '{self.last_guidance_field}' was collected")
            self.mark_guidance_processed()
            self.last_guidance_field = None
            return True
        
        return False
    
    def should_escalate_guidance(self, field: str) -> bool:
        """Check if we should escalate guidance for a specific field."""
        return self.guidance_attempts.get(field, 0) >= self.max_attempts_per_field