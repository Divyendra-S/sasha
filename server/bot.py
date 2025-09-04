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
            "content": """You are a professional technical interviewer conducting a job interview. Your goal is to:

1. Be friendly and conversational while maintaining professionalism
2. Gather information about the candidate's background, experience, and preferences
3. Ask follow-up questions naturally based on their responses
4. Keep the conversation flowing smoothly

Information to collect during the interview:
- Candidate's name and background
- Years of professional experience
- Current role or position they're seeking
- Technical skills and expertise areas
- Salary expectations
- Work preference (remote, hybrid, or onsite)

Adapt your questions based on what the candidate shares. Don't make it feel like an interrogation - let it flow naturally like a conversation. Ask open-ended questions and show interest in their responses.""",
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
        
        # Add a simple user message to start the conversation
        messages.append({
            "role": "user",
            "content": "Hello"
        })
        
        # Start the interview
        messages.append({
            "role": "system", 
            "content": "Greet the candidate warmly and introduce yourself as their interviewer. Ask them to start by telling you about themselves."
        })
        await task.queue_frames([context_aggregator.user().get_context_frame()])

        # Start background task for interview flow management (with delay)
        asyncio.create_task(delayed_flow_monitor(task, flow_manager, messages, context_aggregator))

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("[BOT] Client disconnected")
        logger.info("[INTERVIEW_FINAL] Interview session ended")
        
        # Log final interview status
        collected_fields = interview_data.get_collected_fields()
        missing_fields = interview_data.get_missing_fields()
        completion_status = "COMPLETE" if interview_data.is_complete() else "INCOMPLETE"
        
        logger.info(f"[INTERVIEW_FINAL] Status: {completion_status}")
        logger.info(f"[INTERVIEW_FINAL] Collected: {collected_fields}")
        logger.info(f"[INTERVIEW_FINAL] Missing: {missing_fields}")
        
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False)

    await runner.run(task)


async def delayed_flow_monitor(task, flow_manager, messages, context_aggregator):
    """Start flow monitor after a delay to let initial conversation begin."""
    await asyncio.sleep(120)  # Wait 2 minutes before starting guidance
    await interview_flow_monitor(task, flow_manager, messages, context_aggregator)


async def interview_flow_monitor(task, flow_manager, messages, context_aggregator):
    """Background task that monitors interview progress and provides guidance."""
    logger.info("[INTERVIEW_FLOW] Starting flow monitor")
    
    try:
        while True:
            await asyncio.sleep(60)  # Check every 60 seconds
            
            if flow_manager.should_provide_guidance():
                guidance = flow_manager.get_guidance_message()
                
                if guidance:
                    missing_fields = flow_manager.interview_data.get_missing_fields()
                    logger.info(f"[INTERVIEW_FLOW] Guiding conversation toward missing info: {', '.join(missing_fields)}")
                    
                    # Check if we already have recent guidance to avoid duplicates
                    recent_guidance = [msg for msg in messages[-3:] if msg.get("role") == "system" and "guide" in msg.get("content", "").lower()]
                    
                    if not recent_guidance:
                        # Limit message history to prevent bloating
                        if len(messages) > 20:
                            # Keep the first system message and recent conversation
                            system_msg = messages[0]
                            recent_messages = messages[-15:]
                            messages.clear()
                            messages.append(system_msg)
                            messages.extend(recent_messages)
                        
                        # Add guidance to conversation
                        guidance_message = {
                            "role": "system",
                            "content": f"Subtly guide the conversation to gather this information: {guidance}"
                        }
                        messages.append(guidance_message)
                        
                        # Trigger LLM to incorporate the guidance
                        await task.queue_frames([
                            LLMMessagesAppendFrame([guidance_message], run_llm=True)
                        ])
                
                elif flow_manager.interview_data.is_complete():
                    logger.info("[INTERVIEW_FLOW] Interview complete - wrapping up")
                    completion_message = {
                        "role": "system",
                        "content": "The interview is complete. Thank the candidate and wrap up the conversation professionally."
                    }
                    messages.append(completion_message)
                    await task.queue_frames([
                        LLMMessagesAppendFrame([completion_message], run_llm=True)
                    ])
                    break
                    
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
