"""
Job Description Information Extractor

This module provides a frame processor that extracts structured information
from user speech during job description creation using LLM-based extraction.
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Callable

from loguru import logger
from pipecat.frames.frames import Frame, TextFrame
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.services.openai.llm import OpenAILLMService


@dataclass
class JDData:
    """Data structure to track job description information."""
    
    # Core fields matching frontend
    job_title: Optional[str] = None  # Maps to frontend 'title'
    company_name: Optional[str] = None  # Maps to frontend 'company'
    responsibilities: Optional[str] = None  # Maps to frontend 'description'
    required_qualifications: Optional[str] = None  # Will be split into frontend 'requirements' list
    preferred_qualifications: Optional[str] = None  # Will be split into frontend 'benefits' list
    work_arrangement: Optional[str] = None  # Maps to frontend 'location'
    salary_range: Optional[str] = None  # Maps to frontend 'salaryRange'
    employment_type: Optional[str] = None  # Maps to frontend 'employmentType'
    
    # Additional fields for comprehensive JD creation
    technical_skills: Optional[List[str]] = None
    team_size: Optional[str] = None
    growth_opportunities: Optional[str] = None
    department: Optional[str] = None
    experience_level: Optional[str] = None
    education_requirements: Optional[str] = None
    
    # Internal tracking
    _collected_fields: Set[str] = field(default_factory=set)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _update_callbacks: List[Callable] = field(default_factory=list, init=False, repr=False)
    
    # Extraction event tracking
    _has_new_extraction: bool = field(default=False, init=False, repr=False)
    _last_extraction_time: float = field(default=0.0, init=False, repr=False)
    _extraction_counter: int = field(default=0, init=False, repr=False)
    
    def add_update_callback(self, callback: Callable[[str, any], None]):
        """Add a callback that will be called when any field is updated."""
        self._update_callbacks.append(callback)
        logger.info(f"[JD_DATA] Added update callback, total callbacks: {len(self._update_callbacks)}")
    
    def has_new_extraction(self) -> bool:
        """Check if there are new extractions since last frontend fetch."""
        return self._has_new_extraction
    
    def get_extraction_info(self) -> dict:
        """Get extraction status information."""
        return {
            "hasNewExtraction": self._has_new_extraction,
            "lastExtractionTime": self._last_extraction_time,
            "extractionCounter": self._extraction_counter,
            "totalFields": len(self._collected_fields)
        }
    
    def mark_extraction_consumed(self):
        """Mark that frontend has consumed the extraction updates."""
        self._has_new_extraction = False
        logger.info(f"[JD_DATA] 🔄 Extraction marked as consumed by frontend")
    
    def get_missing_fields(self) -> List[str]:
        """Get list of fields that haven't been collected yet."""
        all_fields = {"job_title", "company_name", "required_qualifications", "responsibilities", 
                     "technical_skills", "preferred_qualifications", "salary_range", "work_arrangement", 
                     "employment_type", "team_size", "growth_opportunities", "department", 
                     "experience_level", "education_requirements"}
        return list(all_fields - self._collected_fields)
    
    def get_all_fields(self) -> List[str]:
        """Get list of all trackable fields."""
        return ["job_title", "company_name", "required_qualifications", "responsibilities", 
               "technical_skills", "preferred_qualifications", "salary_range", "work_arrangement", 
               "employment_type", "team_size", "growth_opportunities", "department", 
               "experience_level", "education_requirements"]
    
    def to_frontend_format(self) -> Dict:
        """Convert JD data to frontend format for the job description editor."""
        # Convert qualifications and benefits to lists
        requirements = []
        if self.required_qualifications:
            requirements = [req.strip() for req in self.required_qualifications.split('\n') if req.strip()]
        if self.technical_skills:
            requirements.extend(self.technical_skills)
        if self.education_requirements:
            requirements.append(self.education_requirements)
        
        benefits = []
        if self.preferred_qualifications:
            benefits = [ben.strip() for ben in self.preferred_qualifications.split('\n') if ben.strip()]
        if self.growth_opportunities:
            benefits.append(self.growth_opportunities)
        
        # Build location string from work arrangement and other details
        location = self.work_arrangement or ""
        if self.department:
            location = f"{self.department}, {location}" if location else self.department
        
        return {
            "title": self.job_title or "",
            "company": self.company_name or "",
            "description": self.responsibilities or "",
            "requirements": requirements,
            "benefits": benefits,
            "location": location.strip(", "),
            "salaryRange": self.salary_range or "",
            "employmentType": self.employment_type or "Full-time",
            # Additional data for debugging/info
            "_extractedFields": list(self._collected_fields),
            "_completionPercentage": len(self._collected_fields) / len(self.get_all_fields()) * 100,
            "_lastUpdate": int(time.time() * 1000)
        }
    
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
                    
                    # Mark new extraction occurred
                    self._has_new_extraction = True
                    self._last_extraction_time = time.time()
                    self._extraction_counter += 1
                    logger.info(f"[JD_DATA] 🚨 NEW EXTRACTION FLAG SET: #{self._extraction_counter}")
                    
                    # Notify callbacks of the update
                    for callback in self._update_callbacks:
                        try:
                            callback(field_name, value)
                        except Exception as e:
                            logger.error(f"[JD_DATA] Error in update callback: {e}")
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
        self._sentence_timeout = 1.5  # seconds to wait before processing buffer
        
        
        self.extraction_prompt = """You are an expert at extracting job description information from conversational text. 

Your job is to extract ANY job-related information from what the user says and return it as a JSON object. Be smart about inferring information even if not explicitly stated.

Available fields to extract:
- job_title: Any job position, role, or title mentioned
- company_name: Company, organization, or business name  
- responsibilities: What the person will do, tasks, duties, job description
- required_qualifications: Must-have skills, experience, certifications, requirements
- technical_skills: Programming languages, technologies, tools, software (as array)
- preferred_qualifications: Nice-to-have skills, bonus qualifications
- salary_range: Pay, compensation, salary, hourly rate, budget
- work_arrangement: Remote, onsite, hybrid, location flexibility
- employment_type: Full-time, part-time, contract, freelance, internship
- team_size: How many people on team, team structure
- experience_level: Junior, senior, entry-level, mid-level, years of experience
- department: Engineering, marketing, sales, HR, which team/division
- education_requirements: Degree requirements, educational background needed
- growth_opportunities: Career advancement, learning opportunities, promotion path

CONTEXT - Current job description state:
{context}

INSTRUCTIONS:
1. Extract ANY relevant information you can find, even partial information
2. Be liberal in your interpretation - if someone says "we need someone good with computers" that could be technical_skills: ["computers"]
3. If you can reasonably infer something, include it
4. Don't be overly strict - extract anything that might be useful
5. Return a valid JSON object with only the fields that have information
6. If absolutely nothing job-related, return empty object {}

USER INPUT: """
    
    async def should_extract(self, text: str) -> bool:
        """Determine if text contains enough information to warrant extraction."""
        if not text or len(text.strip()) < 3:
            return False
        
        # Always extract - let LLM decide what's relevant
        logger.info(f"[EXTRACTION_FILTER] ✅ Will extract from: '{text[:80]}{'...' if len(text) > 80 else ''}'")
        return True
    
    
    
    def get_context_for_llm(self) -> str:
        """Generate context about current JD state for the LLM."""
        collected_fields = self.jd_data.get_collected_fields()
        missing_fields = self.jd_data.get_missing_fields()
        
        context_parts = []
        
        if collected_fields:
            context_parts.append("ALREADY COLLECTED:")
            for field in collected_fields:
                value = getattr(self.jd_data, field, None)
                if value:
                    if isinstance(value, list):
                        context_parts.append(f"  {field}: {value}")
                    else:
                        context_parts.append(f"  {field}: \"{value}\"")
        
        if missing_fields:
            context_parts.append(f"STILL MISSING: {', '.join(missing_fields)}")
        
        if not context_parts:
            return "No information collected yet - extract anything you can find!"
            
        return "\n".join(context_parts)

    async def extract_information(self, text: str) -> Dict:
        """Extract structured information from text using LLM."""
        import time
        extraction_id = f"ext_{int(time.time() * 1000) % 10000}"
        logger.info(f"[EXTRACTION] 🔍 [{extraction_id}] Starting extraction for: \"{text[:80]}{'...' if len(text) > 80 else ''}\"")
        
        try:
            # Get current context
            context = self.get_context_for_llm()
            
            # Build prompt with context
            full_prompt = self.extraction_prompt.replace("{context}", context) + f"\"{text}\""
            
            logger.info(f"[EXTRACTION] [{extraction_id}] Context: {context}")
            
            # Call extraction LLM
            messages = [{"role": "user", "content": full_prompt}]
            
            # Use the LLM service to get extraction results
            logger.info(f"[EXTRACTION] [{extraction_id}] Calling extraction LLM...")
            response_text = await self._call_extraction_llm(messages)
            
            logger.info(f"[EXTRACTION] [{extraction_id}] Raw LLM response: '{response_text[:300]}{'...' if len(response_text) > 300 else ''}'")
            
            # Clean up response - remove markdown code blocks if present
            clean_response = response_text.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]  # Remove ```json
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]  # Remove ```
            clean_response = clean_response.strip()
            
            logger.info(f"[EXTRACTION] [{extraction_id}] Cleaned response: '{clean_response[:300]}{'...' if len(clean_response) > 300 else ''}'")
            
            # Parse JSON response with better error handling
            try:
                extracted_data = json.loads(clean_response)
                if extracted_data:
                    logger.info(f"[EXTRACTION] [{extraction_id}] ✅ Successfully extracted: {list(extracted_data.keys())} -> {extracted_data}")
                else:
                    logger.info(f"[EXTRACTION] [{extraction_id}] No relevant JD information found in user response")
                return extracted_data
            except json.JSONDecodeError as e:
                logger.warning(f"[EXTRACTION] [{extraction_id}] ⚠️ JSON parsing error: {e}")
                logger.warning(f"[EXTRACTION] [{extraction_id}] Raw response was: '{response_text[:500]}...'")
                logger.warning(f"[EXTRACTION] [{extraction_id}] Cleaned response was: '{clean_response[:500]}...'")
                logger.warning(f"[EXTRACTION] [{extraction_id}] Input text was: '{text[:200]}'")
                
                # Try to salvage partial JSON
                try:
                    # Look for JSON-like content in the response
                    import re
                    json_match = re.search(r'\{.*\}', clean_response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        logger.info(f"[EXTRACTION] [{extraction_id}] Attempting to parse extracted JSON: '{json_str[:200]}...'")
                        extracted_data = json.loads(json_str)
                        logger.info(f"[EXTRACTION] [{extraction_id}] 🔄 Recovered from parsing error: {extracted_data}")
                        return extracted_data
                except Exception as recovery_error:
                    logger.warning(f"[EXTRACTION] [{extraction_id}] Could not recover from JSON error: {recovery_error}")
                
                return {}
            
        except Exception as e:
            logger.error(f"[EXTRACTION] [{extraction_id}] ❌ Extraction failed: {str(e)}")
            logger.error(f"[EXTRACTION] [{extraction_id}] Input text: '{text[:100]}'")
            logger.error(f"[EXTRACTION] [{extraction_id}] Prompt length: {len(full_prompt) if 'full_prompt' in locals() else 'unknown'}")
            logger.error(f"[EXTRACTION] [{extraction_id}] JD fields collected: {len(self.jd_data.get_collected_fields())}")
            import traceback
            logger.error(f"[EXTRACTION] [{extraction_id}] Stack trace: {traceback.format_exc()}")
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
                temperature=0.4,  # Higher temperature for better extraction
                max_tokens=800,
                top_p=0.5  # More flexible responses
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
                       "work_arrangement", "employment_type", "team_size", "growth_opportunities",
                       "department", "experience_level", "education_requirements"]
        
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
        """Process frames and extract information from user speech and capture assistant responses."""
        await super().process_frame(frame, direction)
        
        if isinstance(frame, TextFrame):
            text = frame.text.strip()
            if text:
                # User speech (from STT, going downstream)
                if direction == FrameDirection.DOWNSTREAM:
                    logger.info(f"[EXTRACTOR_FRAME] Received user text: '{text}'")
                    await self._add_to_sentence_buffer(text)
                
                # Assistant speech (from LLM, going upstream to TTS)  
                elif direction == FrameDirection.UPSTREAM:
                    logger.info(f"[EXTRACTOR_FRAME] Received assistant text: '{text[:60]}{'...' if len(text) > 60 else ''}'")
                    # Just log assistant messages, no complex history
        
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
        
        # Check if we have a complete sentence or enough text
        combined_text = ' '.join(self._sentence_buffer).strip()
        
        # Process immediately if we have enough meaningful content
        if (len(combined_text) > 15 and 
            (text.endswith('.') or text.endswith('!') or text.endswith('?') or 
             len(combined_text) > 50 or len(self._sentence_buffer) > 8)):
            
            logger.info(f"[SENTENCE_BUFFER] Processing immediately: '{combined_text[:60]}...'")
            self._sentence_buffer.clear()
            
            # Process extraction immediately
            if await self.should_extract(combined_text):
                if len(self._extraction_tasks) < self._max_concurrent_extractions:
                    logger.info(f"[EXTRACTOR_FRAME] Creating immediate extraction task")
                    task = asyncio.create_task(self._extract_and_update_with_cleanup(combined_text))
                    self._extraction_tasks.add(task)
        else:
            # Schedule buffer processing after timeout as fallback
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
        """Generate adaptive guidance message based on missing information."""
        missing_fields = self.jd_data.get_missing_fields()
        collected_fields = self.jd_data.get_collected_fields()
        
        # If we have most information, provide completion guidance
        completion_percentage = len(collected_fields) / len(self.jd_data.get_all_fields())
        
        if not missing_fields:
            return "Excellent! We have all the information needed. The job description is taking shape nicely. Is there anything you'd like to add or refine?"
        
        # Adaptive guidance based on completion percentage
        if completion_percentage < 0.3:  # Less than 30% complete
            # Early stage - ask broad, open-ended questions
            core_missing = [f for f in ["job_title", "company_name", "responsibilities"] if f in missing_fields]
            if core_missing:
                field = core_missing[0]
                if field == "job_title":
                    return "What position are you looking to hire for? Feel free to share as much detail as you'd like about the role."
                elif field == "company_name":
                    return "What's your company name, and can you tell me a bit about what you do?"
                elif field == "responsibilities":
                    return "What would this person be doing day-to-day? What are the key responsibilities?"
        
        elif completion_percentage < 0.7:  # 30-70% complete
            # Middle stage - ask for specific details, but keep it conversational
            important_missing = [f for f in ["required_qualifications", "technical_skills", "salary_range", "work_arrangement"] if f in missing_fields]
            if important_missing:
                field = important_missing[0]
                if field == "required_qualifications":
                    return "What kind of experience or qualifications should candidates have?"
                elif field == "technical_skills":
                    return "Are there specific technical skills or technologies they'll need to know?"
                elif field == "salary_range":
                    return "What's the compensation range you're thinking for this position?"
                elif field == "work_arrangement":
                    return "Is this position remote, in-office, or flexible?"
        
        else:  # Over 70% complete
            # Final stage - ask for nice-to-have details
            remaining = missing_fields[:2]  # Focus on just 1-2 remaining fields
            field_questions = {
                "preferred_qualifications": "Are there any nice-to-have qualifications or skills?",
                "team_size": "What size team would they be working with?",
                "growth_opportunities": "What growth or advancement opportunities does this role offer?",
                "department": "Which department or division is this role in?",
                "experience_level": "What level of seniority are you looking for?",
                "education_requirements": "Any specific educational requirements?",
                "employment_type": "Is this full-time, part-time, or contract?"
            }
            
            for field in remaining:
                if field in field_questions:
                    return field_questions[field]
        
        # Fallback - just ask about the first missing field naturally
        if missing_fields:
            return f"Could you tell me more about the {missing_fields[0].replace('_', ' ')}?"
        
        return None
    
    def should_provide_guidance(self) -> bool:
        """Check if guidance should be provided - much more adaptive approach."""
        import time
        current_time = time.time()
        
        # Don't provide guidance if we're still waiting for a response
        if self.guidance_pending:
            logger.info("[FLOW_GUIDANCE] Skipping - guidance pending response")
            return False
        
        # Calculate completion percentage to determine guidance frequency
        collected_fields = self.jd_data.get_collected_fields()
        completion_percentage = len(collected_fields) / len(self.jd_data.get_all_fields())
        
        # Adaptive guidance intervals based on completion
        if completion_percentage < 0.3:
            guidance_interval = 90  # Longer intervals early on - let natural conversation flow
        elif completion_percentage < 0.7:
            guidance_interval = 75  # Medium intervals in middle phase
        else:
            guidance_interval = 120  # Even longer intervals near completion
        
        # Extended cooldown after sending guidance
        cooldown_time = min(90, guidance_interval)
        
        # Check cooldown period after sending guidance
        if self.last_guidance_field and current_time - self.last_guidance_time < cooldown_time:
            remaining = cooldown_time - (current_time - self.last_guidance_time)
            logger.info(f"[FLOW_GUIDANCE] Adaptive cooldown active - {remaining:.0f}s remaining (completion: {completion_percentage:.0%})")
            return False
        
        # Check if enough time has passed since last guidance
        if current_time - self.last_guidance_time >= guidance_interval:
            logger.info(f"[FLOW_GUIDANCE] Adaptive guidance threshold met - guidance allowed (completion: {completion_percentage:.0%}, interval: {guidance_interval}s)")
            self.last_guidance_time = current_time
            return True
        
        remaining_time = guidance_interval - (current_time - self.last_guidance_time)
        logger.debug(f"[FLOW_GUIDANCE] {remaining_time:.0f}s remaining until next guidance opportunity")
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