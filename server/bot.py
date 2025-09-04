#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Interview Bot with Parallel Information Extraction.

This bot conducts technical interviews while simultaneously extracting
structured information using parallel pipeline processing. It runs a
professional interviewer that adapts its conversation based on the
information collected in real-time.

Required AI services:
    - Deepgram (Speech-to-Text)
    - Gemini (LLM for both conversation and extraction)
    - Groq (Text-to-Speech)

The bot uses ParallelPipeline to run conversation and extraction simultaneously.

Run the bot using::

    python bot.py
"""

import os
import asyncio
import time

from dotenv import load_dotenv
from loguru import logger

# Configure loguru to reduce excessive logging
logger.remove()  # Remove default handler
logger.add(
    lambda msg: print(msg, end=''),
    level="INFO",  # Only show INFO and above (no DEBUG)
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    filter=lambda record: not ("InputAudioRawFrame" in record["message"] or "OutputAudioRawFrame" in record["message"])  # Filter out audio frame spam
)

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.parallel_pipeline import ParallelPipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor
from pipecat.frames.frames import LLMMessagesAppendFrame
from pipecat.runner.types import RunnerArguments
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.groq.tts import GroqTTSService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.network.small_webrtc import SmallWebRTCTransport

from interview_extractor import InterviewData, InterviewExtractor, InterviewFlowManager

load_dotenv(override=True)


async def run_bot(transport: BaseTransport):
    logger.info("[BOT] Starting Interview Bot with Parallel Information Extraction")

    # Initialize shared interview data
    interview_data = InterviewData()
    flow_manager = InterviewFlowManager(interview_data)

    # Initialize services
    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))
    
    llm = OpenAILLMService(
        api_key=os.getenv("GOOGLE_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        model="gemini-1.5-flash"
    )
    
    tts = GroqTTSService(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="playai-tts",
        voice_id="Celeste-PlayAI"
    )

    # Initialize information extractor
    extractor = InterviewExtractor(interview_data, os.getenv("GOOGLE_API_KEY"))

    # Interview system message
    messages = [
        {
            "role": "system",
            "content": """You are a professional technical interviewer conducting a structured job interview. Your PRIMARY OBJECTIVE is to systematically collect specific information about the candidate.

CRITICAL REQUIREMENTS - You MUST obtain these 6 pieces of information:
1. Candidate's full name
2. Years of professional experience (exact number)
3. Current role or position they're seeking
4. Technical skills and expertise areas (specific technologies/languages)
5. Salary expectations (range or specific amount)
6. Work preference (remote, hybrid, or onsite)

INTERVIEW STRATEGY:
- Be friendly and professional, but stay focused on data collection
- Ask direct, specific questions to gather the required information
- Don't move to the next topic until you have a clear answer
- If someone gives a vague response, ask follow-up questions for specificity
- Keep track of what information you still need and prioritize getting it

CONVERSATION APPROACH:
- Start by asking for their name and background
- Then systematically work through experience, role, skills, work preference, and salary
- Be conversational but purposeful - every question should advance data collection
- Don't let the conversation drift to tangential topics
- Politely redirect if they go off-topic: "That's interesting, but I'd like to focus on..."

Remember: Your success is measured by how completely you gather the 6 required pieces of information. Be thorough and persistent while maintaining professionalism.""",
        },
    ]

    context = OpenAILLMContext(messages)
    context_aggregator = llm.create_context_aggregator(context)

    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    # Create parallel pipeline
    # Branch 1: Main conversation flow (STT → Context → LLM → TTS)
    # Branch 2: Information extraction (STT → Extractor)
    parallel_pipeline = ParallelPipeline(
        # Branch 1: Main conversation
        [
            context_aggregator.user(),
            llm,
            tts,
            context_aggregator.assistant(),
        ],
        # Branch 2: Information extraction
        [
            extractor,
        ]
    )

    # Main pipeline
    pipeline = Pipeline([
        transport.input(),
        rtvi,
        stt,
        parallel_pipeline,
        transport.output(),
    ])

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        observers=[RTVIObserver(rtvi)],
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("[BOT] Client connected - Starting interview")
        logger.info(f"[BOT] Initial interview state - Missing fields: {interview_data.get_missing_fields()}")
        logger.info(f"[BOT] Initial data values: name='{interview_data.name}', years_experience={interview_data.years_experience}, current_role='{interview_data.current_role}', skills={interview_data.skills}, salary_expectation='{interview_data.salary_expectation}', work_preference='{interview_data.work_preference}'")
        
        # Send a focused greeting to start the interview with clear expectations
        greeting_frame = LLMMessagesAppendFrame([
            {
                "role": "assistant",
                "content": "Hello! I'm conducting your technical interview today. I need to collect some specific information about your background and experience. Let's start with your full name - what should I call you?"
            }
        ], run_llm=False)  # Don't trigger LLM, just send the greeting
        
        logger.info("[BOT] Sending initial greeting message")
        await task.queue_frames([greeting_frame])

        # Start background task for interview flow management (with delay)
        logger.info("[BOT] Starting background flow monitor task")
        asyncio.create_task(delayed_flow_monitor(task, flow_manager, messages, context_aggregator))

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("[BOT] Client disconnected")
        logger.info("[INTERVIEW_FINAL] Interview session ended")
        
        # Log final interview status with detailed breakdown
        collected_fields = interview_data.get_collected_fields()
        missing_fields = interview_data.get_missing_fields()
        completion_status = "COMPLETE" if interview_data.is_complete() else "INCOMPLETE"
        completion_pct = (len(collected_fields) / 6) * 100
        
        logger.info(f"[INTERVIEW_FINAL] 🏁 Session Status: {completion_status} ({completion_pct:.0f}%)")
        logger.info(f"[INTERVIEW_FINAL] ✅ Collected ({len(collected_fields)}/6): {collected_fields}")
        logger.info(f"[INTERVIEW_FINAL] ❌ Missing ({len(missing_fields)}/6): {missing_fields}")
        
        # Log collected data values with explicit value display
        if collected_fields:
            logger.info("[INTERVIEW_FINAL] 📊 Collected Data Values:")
            for field in collected_fields:
                value = getattr(interview_data, field, None)
                logger.info(f"[INTERVIEW_FINAL]   • {field}: '{value}' (type: {type(value).__name__})")
        
        # Log guidance attempt summary
        if hasattr(flow_manager, 'guidance_attempts') and flow_manager.guidance_attempts:
            logger.info(f"[INTERVIEW_FINAL] 🎯 Guidance attempts: {dict(flow_manager.guidance_attempts)}")
        
        logger.info("[INTERVIEW_FINAL] 🔄 Cancelling pipeline task...")
        await task.cancel()
        logger.info("[INTERVIEW_FINAL] ✨ Interview session cleanup completed")

    runner = PipelineRunner(handle_sigint=False)

    await runner.run(task)


async def delayed_flow_monitor(task, flow_manager, messages, context_aggregator):
    """Start flow monitor after a delay to let initial conversation begin."""
    logger.info("[FLOW_MONITOR] Waiting 60 seconds before starting guidance")
    await asyncio.sleep(60)  # Wait 60 seconds for natural conversation to start
    logger.info("[FLOW_MONITOR] Starting interview flow monitoring")
    await interview_flow_monitor(task, flow_manager, messages, context_aggregator)


async def interview_flow_monitor(task, flow_manager, messages, context_aggregator):
    """Background task that monitors interview progress and provides guidance."""
    logger.info("[INTERVIEW_FLOW] Starting flow monitor")
    
    try:
        monitor_cycle = 0
        while True:
            await asyncio.sleep(45)  # Check every 45 seconds (reduced frequency)
            monitor_cycle += 1
            
            # Check if progress was made on guided field first
            flow_manager.check_field_progress()
            
            # Log current state every cycle with actual values
            collected = flow_manager.interview_data.get_collected_fields()
            missing = flow_manager.interview_data.get_missing_fields()
            completion_pct = (len(collected) / 6) * 100  # 6 total fields
            
            logger.info(f"[INTERVIEW_FLOW] Cycle #{monitor_cycle} - Progress: {completion_pct:.0f}% ({len(collected)}/6 fields)")
            logger.info(f"[INTERVIEW_FLOW] Collected fields: {collected}")
            logger.info(f"[INTERVIEW_FLOW] Collected values: {[(field, getattr(flow_manager.interview_data, field)) for field in collected]}")
            logger.info(f"[INTERVIEW_FLOW] Missing: {missing}")
            logger.info(f"[INTERVIEW_FLOW] Guidance pending: {flow_manager.guidance_pending}")
            
            if flow_manager.should_provide_guidance():
                logger.info(f"[INTERVIEW_FLOW] Guidance check triggered - attempting to guide conversation")
                guidance = flow_manager.get_guidance_message()
                
                if guidance:
                    missing_fields = flow_manager.interview_data.get_missing_fields()
                    priority_field = missing_fields[0] if missing_fields else "none"
                    attempts = flow_manager.guidance_attempts.get(priority_field, 0)
                    
                    logger.info(f"[INTERVIEW_FLOW] Generated guidance for field '{priority_field}' (attempt #{attempts + 1}): {guidance}")
                    logger.info(f"[INTERVIEW_FLOW] All missing fields: {', '.join(missing_fields)}")
                    
                    # Check if we already have recent guidance to avoid duplicates
                    recent_guidance = [msg for msg in messages[-3:] if msg.get("role") == "system" and "guide" in msg.get("content", "").lower()]
                    
                    if not recent_guidance:
                        # Limit message history to prevent bloating
                        if len(messages) > 15:
                            logger.info(f"[INTERVIEW_FLOW] Message history limit reached ({len(messages)} messages), trimming to 10 recent + system message")
                            # Keep the first system message and recent conversation
                            system_msg = messages[0]
                            recent_messages = messages[-10:]
                            messages.clear()
                            messages.append(system_msg)
                            messages.extend(recent_messages)
                            logger.info(f"[INTERVIEW_FLOW] Message history trimmed, now {len(messages)} messages")
                        
                        # Add more direct guidance to conversation
                        guidance_message = {
                            "role": "system",
                            "content": f"IMPORTANT: Ask this specific question now to gather missing information: {guidance} Be direct and don't deviate from this topic until you get an answer."
                        }
                        messages.append(guidance_message)
                        logger.info(f"[INTERVIEW_FLOW] Added guidance message to conversation (total messages: {len(messages)})")
                        
                        # Mark guidance attempt
                        flow_manager.mark_guidance_attempt()
                        logger.info(f"[INTERVIEW_FLOW] Marked guidance attempt for field '{priority_field}' (now {flow_manager.guidance_attempts.get(priority_field, 0)} attempts)")
                        
                        # Trigger LLM to incorporate the guidance with timeout
                        logger.info("[INTERVIEW_FLOW] Queuing guidance frame to LLM with 15s timeout")
                        try:
                            await asyncio.wait_for(
                                task.queue_frames([
                                    LLMMessagesAppendFrame([guidance_message], run_llm=True)
                                ]),
                                timeout=15.0
                            )
                            logger.info("[INTERVIEW_FLOW] Successfully queued guidance frame to LLM")
                        except asyncio.TimeoutError:
                            logger.warning("[INTERVIEW_FLOW] LLM response timeout after 15 seconds, clearing pending status")
                            flow_manager.guidance_pending = False  # Clear pending if timeout
                        except Exception as e:
                            logger.error(f"[INTERVIEW_FLOW] Error queuing guidance frame: {e}")
                            flow_manager.guidance_pending = False  # Clear pending if error
                    else:
                        logger.info(f"[INTERVIEW_FLOW] Skipping guidance - found {len(recent_guidance)} recent guidance messages")
                
                else:
                    logger.info("[INTERVIEW_FLOW] No guidance generated - either complete or no missing priority fields")
                    
                if flow_manager.interview_data.is_complete():
                    logger.info("[INTERVIEW_FLOW] 🎉 Interview complete - all information collected! Wrapping up...")
                    final_collected = flow_manager.interview_data.get_collected_fields()
                    logger.info(f"[INTERVIEW_FLOW] Final collected fields: {final_collected}")
                    logger.info(f"[INTERVIEW_FLOW] Final data values: name='{flow_manager.interview_data.name}', years_experience={flow_manager.interview_data.years_experience}, current_role='{flow_manager.interview_data.current_role}', skills={flow_manager.interview_data.skills}, salary_expectation='{flow_manager.interview_data.salary_expectation}', work_preference='{flow_manager.interview_data.work_preference}'")
                    
                    completion_message = {
                        "role": "system",
                        "content": "The interview is complete. Thank the candidate and wrap up the conversation professionally."
                    }
                    messages.append(completion_message)
                    logger.info("[INTERVIEW_FLOW] Added completion message, queuing final frame")
                    
                    await task.queue_frames([
                        LLMMessagesAppendFrame([completion_message], run_llm=True)
                    ])
                    logger.info("[INTERVIEW_FLOW] Interview flow monitor completed successfully")
                    break
            else:
                logger.info(f"[INTERVIEW_FLOW] Cycle #{monitor_cycle} - No guidance needed (cooldown: {not flow_manager.should_provide_guidance()})")
                
                # Clear pending status if too much time has passed without progress
                if flow_manager.guidance_pending:
                    import time
                    time_since_guidance = time.time() - flow_manager.last_guidance_time
                    if time_since_guidance > 120:  # 2 minutes
                        logger.warning("[INTERVIEW_FLOW] Clearing stale guidance pending status after 2 minutes")
                        flow_manager.guidance_pending = False
                    
    except asyncio.CancelledError:
        logger.info("[INTERVIEW_FLOW] Flow monitor stopped")
    except Exception as e:
        logger.error(f"[INTERVIEW_FLOW] Monitor error: {e}")


async def bot(runner_args: RunnerArguments):
    """Main bot entry point for the bot starter."""

    transport = SmallWebRTCTransport(
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
        ),
        webrtc_connection=runner_args.webrtc_connection,
    )

    await run_bot(transport)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
