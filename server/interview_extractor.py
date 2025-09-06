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
    location: Optional[str] = None  # Maps to frontend 'location' - actual location/address
    work_arrangement: Optional[str] = None  # Remote/hybrid/onsite work style
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
                     "technical_skills", "preferred_qualifications", "salary_range", "location", "work_arrangement", 
                     "employment_type", "team_size", "growth_opportunities", "department", 
                     "experience_level", "education_requirements"}
        return list(all_fields - self._collected_fields)
    
    def get_all_fields(self) -> List[str]:
        """Get list of all trackable fields."""
        return ["job_title", "company_name", "required_qualifications", "responsibilities", 
               "technical_skills", "preferred_qualifications", "salary_range", "location", "work_arrangement", 
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
        
        # Use location field directly - don't mix with work_arrangement or department
        location = self.location or ""
        
        return {
            "title": self.job_title or "",
            "company": self.company_name or "",
            "description": self.responsibilities or "",
            "requirements": requirements,
            "benefits": benefits,
            "location": location,
            "workArrangement": self.work_arrangement or "",
            "salaryRange": self.salary_range or "",
            "employmentType": self.employment_type or "Full-time",
            "experienceLevel": self.experience_level or "",
            "department": self.department or "",
            "teamSize": self.team_size or "",
            "technicalSkills": self.technical_skills or [],
            "educationRequirements": self.education_requirements or "",
            "growthOpportunities": self.growth_opportunities or "",
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
        
        # Conversation history for context-aware extraction
        self._conversation_history = []
        self._max_history_size = 6  # Keep last 6 messages for context
        
        
        self.extraction_prompt = """You extract job description information. Be EXTREMELY careful about field relevance. Return ONLY valid JSON.

FIELD VALIDATION RULES - Only extract if text CLEARLY matches the field:

job_title: ONLY job positions/roles (✓ "Software Engineer", "Manager", "Developer" ✗ "location building", "my company", "remote")
company_name: ONLY organization names (✓ "Google", "TechCorp", "Devin Inc" ✗ "AI company", "location building", "engineering")  
responsibilities: ONLY job duties/tasks (✓ "manage team", "write code", "design systems" ✗ "Python", "5 years", "remote")
required_qualifications: ONLY mandatory skills/experience (✓ "5 years Python", "CS degree" ✗ "nice to have", "preferred")
technical_skills: ONLY technologies/languages as array (✓ ["Python", "React"] ✗ "good with computers", "5 years experience")
location: ONLY physical places (✓ "San Francisco", "New York office", "Building 5" ✗ "remote", "hybrid", "flexible")
work_arrangement: ONLY work style (✓ "remote", "hybrid", "onsite" ✗ "San Francisco", "office building")
salary_range: ONLY compensation (✓ "$100k", "80-120k" ✗ "negotiable", "good benefits")
experience_level: ONLY seniority (✓ "senior", "junior", "mid-level" ✗ "Python", "5 years")

CONVERSATION CONTEXT:
{conversation_context}

CURRENT COLLECTED DATA:
{current_data}

VALIDATION RULES:
1. If user input doesn't clearly match a field's purpose, DON'T extract it
2. Consider what question was likely asked based on conversation context
3. Only extract if you're 90% confident the text belongs in that field
4. When in doubt, return empty {} rather than guess wrong
5. Don't extract same information twice

EXAMPLES:
Bot: "What's the job title?" User: "location building" → {} (not a job title)
Bot: "What's your company?" User: "It is my company's name is Devin" → {"company_name": "Devin"}  
Bot: "What technologies?" User: "Python and React" → {"technical_skills": ["Python", "React"]}

INPUT TO ANALYZE: """
    
    async def should_extract(self, text: str) -> bool:
        """Determine if text contains enough information to warrant extraction."""
        if not text or len(text.strip()) < 3:
            return False
        
        # Always extract - let LLM decide what's relevant
        logger.info(f"[EXTRACTION_FILTER] ✅ Will extract from: '{text[:80]}{'...' if len(text) > 80 else ''}'")
        return True
    
    def add_to_conversation_history(self, role: str, message: str):
        """Add a message to conversation history for extraction context."""
        if message and message.strip():
            self._conversation_history.append({"role": role, "content": message.strip()})
            # Keep only recent messages
            if len(self._conversation_history) > self._max_history_size:
                self._conversation_history = self._conversation_history[-self._max_history_size:]
            logger.info(f"[CONVERSATION_HISTORY] Added {role} message, history size: {len(self._conversation_history)}")
    
    def get_conversation_context(self) -> str:
        """Get recent conversation context to help with extraction."""
        if not self._conversation_history:
            return "No conversation context available"
        
        context_lines = ["RECENT CONVERSATION:"]
        for msg in self._conversation_history[-4:]:  # Last 4 messages
            role = "Bot" if msg["role"] == "assistant" else "User"
            content = msg["content"][:120] + "..." if len(msg["content"]) > 120 else msg["content"]
            context_lines.append(f"{role}: {content}")
        
        return "\n".join(context_lines)
    
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
            # Add user input to conversation history for context
            self.add_to_conversation_history("user", text)
            
            # Get conversation context and current data
            conversation_context = self.get_conversation_context()
            current_data = self.get_context_for_llm()
            
            # Build prompt with both contexts
            full_prompt = self.extraction_prompt.replace("{conversation_context}", conversation_context)
            full_prompt = full_prompt.replace("{current_data}", current_data) + f"\"{text}\""
            
            logger.info(f"[EXTRACTION] [{extraction_id}] Conversation context: {conversation_context[:200]}...")
            logger.info(f"[EXTRACTION] [{extraction_id}] Current data: {current_data[:200]}...")
            
            # Call extraction LLM
            messages = [{"role": "user", "content": full_prompt}]
            
            # Use the LLM service to get extraction results
            logger.info(f"[EXTRACTION] [{extraction_id}] Calling extraction LLM...")
            response_text = await self._call_extraction_llm(messages)
            
            logger.info(f"[EXTRACTION] [{extraction_id}] Raw LLM response: '{response_text[:300]}{'...' if len(response_text) > 300 else ''}'")
            
            # Clean up response - remove markdown code blocks and extra text
            clean_response = response_text.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]  # Remove ```json
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]  # Remove ```
            clean_response = clean_response.strip()
            
            # If response contains JSON followed by explanation, extract only JSON
            import re
            json_match = re.search(r'^(\{.*?\})', clean_response, re.DOTALL)
            if json_match:
                clean_response = json_match.group(1).strip()
            else:
                # Try to find JSON anywhere in the response
                json_match = re.search(r'\{.*?\}', clean_response, re.DOTALL)
                if json_match:
                    clean_response = json_match.group(0).strip()
            
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
    
    def validate_field_content(self, field: str, value: str) -> bool:
        """Validate if the extracted value actually belongs in the given field."""
        if not value or not isinstance(value, str):
            return False
        
        value_lower = value.lower().strip()
        
        # Field-specific validation rules
        if field == "job_title":
            # Job titles should not contain location words, company descriptions, or work arrangements
            invalid_patterns = ["location", "building", "office", "remote", "onsite", "hybrid", "company", "my company"]
            if any(pattern in value_lower for pattern in invalid_patterns):
                logger.warning(f"[FIELD_VALIDATION] Rejecting job_title '{value}' - contains invalid pattern")
                return False
            # Should contain role-related words
            valid_patterns = ["engineer", "developer", "manager", "analyst", "designer", "architect", "lead", "senior", "junior", "director", "specialist", "coordinator"]
            if len(value_lower) > 3 and not any(pattern in value_lower for pattern in valid_patterns) and not any(c.isupper() for c in value):
                logger.warning(f"[FIELD_VALIDATION] Rejecting job_title '{value}' - doesn't look like a job title")
                return False
                
        elif field == "company_name":
            # Company names should not be descriptions or locations
            invalid_patterns = ["location", "building", "office", "my company's name is", "it is", "the company"]
            if any(pattern in value_lower for pattern in invalid_patterns):
                logger.warning(f"[FIELD_VALIDATION] Rejecting company_name '{value}' - contains invalid pattern")
                return False
                
        elif field == "location":
            # Locations should not be work arrangements
            if value_lower in ["remote", "onsite", "hybrid", "flexible"]:
                logger.warning(f"[FIELD_VALIDATION] Rejecting location '{value}' - this is work_arrangement")
                return False
                
        elif field == "work_arrangement":
            # Work arrangements should only be these specific values
            valid_arrangements = ["remote", "onsite", "hybrid", "flexible", "in-office", "work from home"]
            if not any(arr in value_lower for arr in valid_arrangements):
                logger.warning(f"[FIELD_VALIDATION] Rejecting work_arrangement '{value}' - not a valid arrangement")
                return False
        
        return True

    async def update_jd_data(self, extracted_data: Dict) -> None:
        """Update JD data with extracted information after validation."""
        updates_made = []
        ignored_fields = []
        validation_rejects = []
        
        logger.info(f"[EXTRACTION_UPDATE] Processing extracted JD data: {extracted_data}")
        
        valid_fields = ["job_title", "company_name", "required_qualifications", "responsibilities", 
                       "technical_skills", "preferred_qualifications", "salary_range", "location",
                       "work_arrangement", "employment_type", "team_size", "growth_opportunities",
                       "department", "experience_level", "education_requirements"]
        
        for field, value in extracted_data.items():
            if field in valid_fields:
                # Validate field content before updating
                if isinstance(value, str) and not self.validate_field_content(field, value):
                    validation_rejects.append(f"{field}='{value}'")
                    logger.warning(f"[EXTRACTION_UPDATE] ❌ Rejected {field} = '{value}' (failed validation)")
                    continue
                    
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
        
        if validation_rejects:
            logger.info(f"[EXTRACTION_UPDATE] Rejected {len(validation_rejects)} fields due to validation: {validation_rejects}")
            
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
                    # Add assistant message to conversation history for context
                    self.add_to_conversation_history("assistant", text)
        
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