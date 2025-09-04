# Interview Bot with Parallel Information Extraction

This implementation creates an interview bot that conducts natural conversations while simultaneously extracting structured information from user responses using a parallel pipeline architecture.

## Features

### 🤖 Interview Bot
- Professional technical interviewer persona
- Natural conversation flow that adapts to missing information
- Dynamic prompting based on collected data
- Comprehensive logging throughout the process

### 🔄 Parallel Processing
- **Branch 1**: Main conversation (STT → LLM → TTS)
- **Branch 2**: Information extraction (STT → Information Extractor)
- Both branches run simultaneously without blocking each other

### 📊 Information Extraction
- Conditional processing (only extracts when user provides substantial information)
- LLM-based extraction using Gemini for context-aware parsing
- Tracks: name, experience, salary, work preference, skills, current role
- Real-time logging of extraction events and data updates

### 🎯 Dynamic Flow Management
- Background task monitors interview progress every 30 seconds
- Provides guidance to bot based on missing information
- Automatically completes interview when all data is collected

## Architecture

```
Client ←→ WebRTC Transport
           ↓
    ParallelPipeline
    ├── Branch 1: [RTVI → STT → Context → Interview LLM → TTS → Context]
    └── Branch 2: [STT → Information Extractor (Gemini LLM)]
           ↓
    Interview Data Dictionary
```

## Files

- `bot.py` - Main bot implementation with parallel pipeline
- `interview_extractor.py` - Information extraction processor and data structures
- `test_mock_extraction.py` - Mock tests (no API keys required)
- `test_extraction.py` - Full tests with real LLM calls
- `validate_setup.py` - Setup validation script

## Setup

1. **Install dependencies:**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables in `.env`:**
   ```
   DEEPGRAM_API_KEY=your_deepgram_key
   GOOGLE_API_KEY=your_gemini_key  
   GROQ_API_KEY=your_groq_key
   ```

3. **Validate setup:**
   ```bash
   python validate_setup.py
   ```

## Testing

### Mock Testing (No API Keys Required)
```bash
python test_mock_extraction.py
```
- Tests conditional processing logic
- Tests data collection and tracking
- Tests interview completion detection
- Comprehensive logging verification

### Full Testing (Requires API Keys)
```bash
python test_extraction.py
```
- Tests real LLM extraction calls
- Validates JSON parsing
- Tests error handling

### Validation
```bash
python validate_setup.py
```
- Checks file structure
- Validates environment variables
- Tests imports and basic functionality

## Running the Bot

```bash
source venv/bin/activate
python bot.py
```

The bot will start and wait for client connections at http://localhost:7860/client

When a client connects:
1. Bot introduces itself as a technical interviewer
2. Parallel extraction begins processing user responses (after 2 minutes)
3. Dynamic flow management guides conversation toward missing info (every 60 seconds)
4. Interview completes when all required information is collected

### Flow Management
- Initial conversation starts immediately without guidance
- Background monitoring begins after 2 minutes to allow natural conversation
- Guidance is provided every 60 seconds if information is missing
- Message history is automatically managed to prevent API issues

## Logging

The system provides comprehensive logging with prefixes:
- `[BOT]` - Main bot events
- `[EXTRACTION]` - Information extraction events  
- `[INTERVIEW_DATA]` - Data updates
- `[INTERVIEW_STATUS]` - Progress tracking
- `[INTERVIEW_FLOW]` - Dynamic conversation management
- `[INTERVIEW_FINAL]` - Session completion

### Example Log Output
```
[EXTRACTION] Triggered for: "My name is John and I have 5 years experience"
[EXTRACTION] LLM Response: {"name": "John", "years_experience": 5}
[INTERVIEW_DATA] Updated: name = John
[INTERVIEW_DATA] Updated: years_experience = 5
[INTERVIEW_STATUS] Collected: ['name', 'years_experience'] | Missing: ['current_role', 'skills', 'salary_expectation', 'work_preference']
[INTERVIEW_FLOW] Guiding conversation toward missing info: current_role, skills, salary_expectation, work_preference
```

## Collected Information

The system tracks:
- **name**: Full name of the candidate
- **years_experience**: Total years of professional experience
- **current_role**: Current job title/position
- **skills**: List of technical skills and expertise
- **salary_expectation**: Expected salary range
- **work_preference**: Remote, hybrid, or onsite preference

## Error Handling

- Graceful handling of LLM failures
- JSON parsing error recovery
- Concurrent access protection with async locks
- Comprehensive error logging
- Fallback behavior for missing data

## Performance

- Non-blocking parallel processing
- Conditional extraction (avoids processing "yes", "no", etc.)
- Efficient filtering of short responses
- Minimal impact on conversation flow
- Real-time data updates

## Customization

- Modify `InterviewData` class to track additional fields
- Update extraction prompt for different information types
- Adjust flow management timing and logic
- Customize interview bot personality and questions