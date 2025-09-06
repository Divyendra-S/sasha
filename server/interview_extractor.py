"""
Job Description Information Extractor

This module provides a frame processor that extracts structured information
from user speech during job description creation using LLM-based extraction.
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
class JDData:
    """Data structure to track job description information."""
    
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    required_qualifications: Optional[str] = None
    responsibilities: Optional[str] = None
    technical_skills: Optional[List[str]] = None
    preferred_qualifications: Optional[str] = None
    salary_range: Optional[str] = None
    work_arrangement: Optional[str] = None
    team_size: Optional[str] = None
    growth_opportunities: Optional[str] = None
    
    # Internal tracking
    _collected_fields: Set[str] = field(default_factory=set)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    
    def get_missing_fields(self) -> List[str]:
        """Get list of fields that haven't been collected yet."""
        all_fields = {"job_title", "company_name", "required_qualifications", "responsibilities", "technical_skills", "preferred_qualifications", "salary_range", "work_arrangement", "team_size", "growth_opportunities"}
        return list(all_fields - self._collected_fields)
    
    def get_all_fields(self) -> List[str]:
        """Get list of all trackable fields."""
        return ["job_title", "company_name", "required_qualifications", "responsibilities", "technical_skills", "preferred_qualifications", "salary_range", "work_arrangement", "team_size", "growth_opportunities"]
    
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
                
                total_fields = len(self.get_all_fields())
                if old_value != value:
                    logger.info(f"[JD_DATA] ✨ COLLECTED: {field_name} = '{value}' (was: {old_value})")
                    completion_pct = (len(self._collected_fields) / total_fields) * 100
                    logger.info(f"[JD_DATA] Progress: {completion_pct:.0f}% complete ({len(self._collected_fields)}/{total_fields} fields)")
                    logger.info(f"[JD_DATA] Still missing: {self.get_missing_fields()}")
                    
                    # Console log for client-side visibility
                    print(f"\n🎯 CLIENT CONSOLE: JOB DESCRIPTION DATA COLLECTED")
                    print(f"📊 Field: {field_name}")  
                    print(f"💾 Value: {value}")
                    print(f"📈 Progress: {completion_pct:.0f}% ({len(self._collected_fields)}/{total_fields} fields)")
                    print(f"❌ Missing: {self.get_missing_fields()}\n")
                else:
                    logger.info(f"[JD_DATA] Confirmed existing value for {field_name}: '{value}'")
                return True
            else:
                logger.debug(f"[JD_DATA] Skipped empty/null value for {field_name}: {value}")
            return False


class JDExtractor(FrameProcessor):
    """
    Frame processor that extracts structured information from user speech.
    
    This processor runs in parallel with the main conversation flow and
    extracts job description-relevant information using an LLM.
    """
    
    def __init__(self, jd_data: JDData, api_key: str):
        super().__init__()
        self.jd_data = jd_data
        self._extraction_tasks = set()  # Track active extraction tasks
        self._max_concurrent_extractions = 3  # Limit concurrent extractions
        self.api_key = api_key  # Store API key for direct Groq calls
        
        # Sentence buffer to accumulate speech fragments
        self._sentence_buffer = []
        self._last_text_time = 0
        self._sentence_timeout = 3.0  # seconds to wait before processing buffer
        
        self.extraction_prompt = """
You are an information extraction system for job description creation. Extract structured information from hiring manager responses.

Extract the following fields from the user's response (only if explicitly mentioned):
- job_title: The job title/position being created (e.g., "Senior Software Engineer", "Marketing Manager")
- company_name: Name of the company
- required_qualifications: Required education, experience, or certifications
- responsibilities: Key job duties and responsibilities
- technical_skills: List of required technical skills, programming languages, tools, or technologies
- preferred_qualifications: Nice-to-have qualifications or experience
- salary_range: Salary range or compensation details
- work_arrangement: Work setup (remote, hybrid, onsite)
- team_size: Size of the team or reporting structure
- growth_opportunities: Career development or growth opportunities

Return ONLY a JSON object with the extracted fields. If no relevant information is found, return an empty JSON object {}.

Examples:
User: "We're looking to hire a Senior React Developer for our fintech startup"
Response: {"job_title": "Senior React Developer", "company_name": "fintech startup"}

User: "They need 5+ years of experience with React, Node.js, and TypeScript. Remote work is fine."
Response: {"required_qualifications": "5+ years of experience", "technical_skills": ["React", "Node.js", "TypeScript"], "work_arrangement": "remote"}

User: "The salary range is $120k to $150k"
Response: {"salary_range": "$120k to $150k"}

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
        
        # Only extract if it might contain meaningful JD info
        has_potential_info = any(keyword in text_lower for keyword in [
            'job', 'title', 'position', 'role', 'company', 'experience', 'year', 'skill', 'salary', 'compensation',
            'remote', 'hybrid', 'onsite', 'team', 'developer', 'engineer', 'manager', 'analyst', 'specialist',
            'python', 'javascript', 'java', 'react', 'node', 'aws', 'kubernetes', 'docker', 'responsibilities',
            'qualifications', 'requirements', 'bachelor', 'master', 'degree', 'certification'
        ])
        
        if not has_potential_info and len(text.split()) < 3:
            logger.debug(f"[EXTRACTION_FILTER] No meaningful content detected: '{text}'")
            return False
        
        logger.info(f"[EXTRACTION_FILTER] ✅ Will extract from: '{text[:80]}{'...' if len(text) > 80 else ''}' (length: {len(text.strip())})")
        return True
    
    async def extract_information(self, text: str) -> Dict:
        """Extract structured information from text using LLM."""
        try:
            logger.info(f"[EXTRACTION] 🔍 Processing JD input: \"{text[:80]}{'...' if len(text) > 80 else ''}\"")
            
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
                logger.info("[EXTRACTION] No relevant JD information found in user response")
            
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
        """Helper method to call the extraction LLM using Groq API."""
        try:
            logger.info("[EXTRACTION_LLM] Making actual Groq LLM call for information extraction")
            
            # Use OpenAI SDK with Groq endpoint
            import openai
            
            # Create client with Groq endpoint
            client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            
            logger.info(f"[EXTRACTION_LLM] Sending {len(messages)} messages to Groq")
            
            # Make the API call using Llama model
            response = await client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content or "{}"
            logger.info(f"[EXTRACTION_LLM] Groq response: {response_text}")
            return response_text
            
        except Exception as e:
            logger.error(f"[EXTRACTION_LLM] Groq call failed: {e}")
            return "{}"
    
    async def update_jd_data(self, extracted_data: Dict) -> None:
        """Update JD data with extracted information."""
        updates_made = []
        ignored_fields = []
        
        logger.info(f"[EXTRACTION_UPDATE] Processing extracted JD data: {extracted_data}")
        
        valid_fields = ["job_title", "company_name", "required_qualifications", "responsibilities", 
                       "technical_skills", "preferred_qualifications", "salary_range", 
                       "work_arrangement", "team_size", "growth_opportunities"]
        
        for field, value in extracted_data.items():
            if field in valid_fields:
                logger.info(f"[EXTRACTION_UPDATE] Attempting to update field '{field}' with value: {value}")
                was_updated = await self.jd_data.update_field(field, value)
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
            collected = self.jd_data.get_collected_fields()
            missing = self.jd_data.get_missing_fields()
            total_fields = len(self.jd_data.get_all_fields())
            
            logger.info(f"[JD_STATUS] 📈 UPDATED {len(updates_made)} field(s): {updates_made}")
            logger.info(f"[JD_STATUS] Total collected fields with values: {[(field, getattr(self.jd_data, field)) for field in collected]} ({len(collected)}/{total_fields})")
            logger.info(f"[JD_STATUS] Still missing: {missing}")
            
            if self.jd_data.is_complete():
                logger.info("[JD_STATUS] 🎉 ALL JD INFORMATION COLLECTED! Job description ready for completion.")
        else:
            logger.info("[EXTRACTION_UPDATE] No valid updates made from extracted data")
    
    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        """Process frames and extract information from user speech."""
        await super().process_frame(frame, direction)
        
        # Only process TextFrames from STT (user speech)
        if isinstance(frame, TextFrame) and direction == FrameDirection.DOWNSTREAM:
            text = frame.text.strip()
            if text:
                logger.info(f"[EXTRACTOR_FRAME] Received JD creation text: '{text}'")
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
                await self.update_jd_data(extracted_data)
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


class JDFlowManager:
    """
    Manages the job description creation flow and provides guidance based on collected information.
    """
    
    def __init__(self, jd_data: JDData):
        self.jd_data = jd_data
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
        missing_fields = self.jd_data.get_missing_fields()
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
        missing_fields = self.jd_data.get_missing_fields()
        if self.last_guidance_field not in missing_fields:
            logger.info(f"[FLOW_GUIDANCE] ✅ Progress made! Field '{self.last_guidance_field}' was collected")
            self.mark_guidance_processed()
            self.last_guidance_field = None
            return True
        
        return False
    
    def should_escalate_guidance(self, field: str) -> bool:
        """Check if we should escalate guidance for a specific field."""
        return self.guidance_attempts.get(field, 0) >= self.max_attempts_per_field


# Backward compatibility aliases
InterviewData = JDData
InterviewExtractor = JDExtractor  
InterviewFlowManager = JDFlowManager