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
                    
                    # Console log for client-side visibility
                    print(f"\n🎯 CLIENT CONSOLE: INTERVIEW DATA COLLECTED")
                    print(f"📊 Field: {field_name}")  
                    print(f"💾 Value: {value}")
                    print(f"📈 Progress: {completion_pct:.0f}% ({len(self._collected_fields)}/6 fields)")
                    print(f"❌ Missing: {self.get_missing_fields()}\n")
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
        self.api_key = api_key  # Store API key for direct Gemini calls
        
        # Sentence buffer to accumulate speech fragments
        self._sentence_buffer = []
        self._last_text_time = 0
        self._sentence_timeout = 3.0  # seconds to wait before processing buffer
        
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
        if not text or len(text.strip()) < 5:  # Minimum 5 characters
            logger.debug(f"[EXTRACTION_FILTER] Too short: '{text}' (length: {len(text.strip()) if text else 0})")
            return False
        
        # Skip common meaningless fragments
        text_lower = text.lower().strip()
        skip_phrases = ['hello', 'hi', 'yeah', 'yes', 'no', 'ok', 'okay', 'um', 'uh', 'the wind', 'income']
        if text_lower in skip_phrases or len(text.split()) < 2:
            logger.debug(f"[EXTRACTION_FILTER] Skipping common phrase or single word: '{text}'")
            return False
        
        # Only extract if it might contain meaningful info (names, numbers, tech terms)
        has_potential_info = any(keyword in text_lower for keyword in [
            'name', 'experience', 'year', 'work', 'skill', 'salary', 'remote', 'hybrid', 'onsite',
            'developer', 'engineer', 'python', 'javascript', 'java', 'react', 'node'
        ])
        
        if not has_potential_info and len(text.split()) < 3:
            logger.debug(f"[EXTRACTION_FILTER] No meaningful content detected: '{text}'")
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
            
            # Clean up response - remove markdown code blocks if present
            clean_response = response_text.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]  # Remove ```json
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]  # Remove ```
            clean_response = clean_response.strip()
            
            logger.info(f"[EXTRACTION] Cleaned response: '{clean_response}'")
            
            # Parse JSON response
            extracted_data = json.loads(clean_response)
            
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
        """Helper method to call the extraction LLM using Google GenAI SDK."""
        try:
            logger.info("[EXTRACTION_LLM] Making actual Gemini LLM call for information extraction")
            
            # Use Google GenAI SDK directly
            from google import genai
            
            # Create client with API key
            client = genai.Client(api_key=self.api_key)
            
            # Convert messages to content text (combine all messages into one prompt)
            content_parts = []
            for msg in messages:
                if msg.get('role') == 'user':
                    content_parts.append(msg.get('content', ''))
            
            full_content = '\n\n'.join(content_parts)
            logger.info(f"[EXTRACTION_LLM] Sending content to Gemini: {full_content[:200]}...")
            
            # Make the API call using Gemini 2.5 Flash (recommended for 2025)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_content,
                config=genai.types.GenerateContentConfig(
                    temperature=0.1,  # Low temperature for consistent extraction
                    max_output_tokens=500,
                    candidate_count=1
                )
            )
            
            response_text = response.text or "{}"
            logger.info(f"[EXTRACTION_LLM] Gemini response: {response_text}")
            return response_text
            
        except Exception as e:
            logger.error(f"[EXTRACTION_LLM] Gemini call failed: {e}")
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
            if text:
                logger.info(f"[EXTRACTOR_FRAME] Received user text: '{text}'")
                await self._add_to_sentence_buffer(text)
        
        # Always pass frame through
        await self.push_frame(frame, direction)
    
    async def _add_to_sentence_buffer(self, text: str):
        """Add text to sentence buffer and process when complete."""
        import time
        current_time = time.time()
        
        # Add text to buffer
        self._sentence_buffer.append(text)
        self._last_text_time = current_time
        
        logger.info(f"[SENTENCE_BUFFER] Added: '{text}' (buffer size: {len(self._sentence_buffer)})")
        
        # Schedule buffer processing after timeout
        asyncio.create_task(self._process_buffer_after_delay())
    
    async def _process_buffer_after_delay(self):
        """Process buffer after delay if no new text arrives."""
        await asyncio.sleep(self._sentence_timeout)
        
        import time
        if time.time() - self._last_text_time >= self._sentence_timeout and self._sentence_buffer:
            # Combine buffer into sentence
            combined_text = ' '.join(self._sentence_buffer).strip()
            self._sentence_buffer.clear()
            
            logger.info(f"[SENTENCE_BUFFER] Processing combined text: '{combined_text}'")
            
            # Check if we should extract from combined text
            should_extract = await self.should_extract(combined_text)
            
            if should_extract:
                # Check if we have too many concurrent extractions
                if len(self._extraction_tasks) >= self._max_concurrent_extractions:
                    logger.warning(f"[EXTRACTOR_FRAME] Too many concurrent extractions ({len(self._extraction_tasks)}), skipping: '{combined_text}'")
                else:
                    logger.info(f"[EXTRACTOR_FRAME] Creating background extraction task for: '{combined_text}'")
                    # Extract information in the background
                    task = asyncio.create_task(self._extract_and_update_with_cleanup(combined_text))
                    self._extraction_tasks.add(task)
            else:
                logger.info(f"[EXTRACTOR_FRAME] Skipping extraction from combined text")
    
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