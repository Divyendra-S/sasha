#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Job Description Creation Bot with Information Extraction.

This bot helps create comprehensive job descriptions by guiding
hiring managers through a structured conversation and extracting
structured information. It runs a professional HR assistant that
guides users through the complete JD creation process.

Required AI services:
    - Groq (Speech-to-Text)
    - Gemini (LLM for both conversation and extraction)
    - Groq (Text-to-Speech)

The bot uses parallel processing to extract JD information in real-time.

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
from pipecat.runner.types import SmallWebRTCRunnerArguments
from pipecat.services.groq.stt import GroqSTTService
from pipecat.services.groq.tts import GroqTTSService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.network.small_webrtc import SmallWebRTCTransport

from interview_extractor import JDData, JDExtractor, JDFlowManager
from jd_api_server import JDAPIServer
from jd_broadcaster import JDDataBroadcaster, create_jd_data_callback

load_dotenv(override=True)


async def run_bot(transport: BaseTransport):
    logger.info("[BOT] Starting Job Description Creation Bot with Information Extraction")

    # Initialize shared JD data
    jd_data = JDData()
    flow_manager = JDFlowManager(jd_data)
    
    # Start API server for JD data access
    api_server = JDAPIServer(jd_data, port=7861)
    api_server.start()

    # Initialize services with better configuration for complete sentences
    stt = GroqSTTService(
        api_key=os.getenv("GROQ_API_KEY")
    )
    
    llm = OpenAILLMService(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
        model="llama-3.3-70b-versatile"
    )
    
    tts = GroqTTSService(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="playai-tts",
        voice_id="Celeste-PlayAI"
    )

    # Initialize JD information extractor
    extractor = JDExtractor(jd_data, os.getenv("GROQ_API_KEY"))

    # Job Description creation system message (dynamic)
    logger.info("[BOT] 🎯 INITIALIZING JOB DESCRIPTION CREATION BOT")
    
    def get_dynamic_system_prompt(jd_data: JDData) -> str:
        """Generate a dynamic system prompt that includes current JD status."""
        collected_fields = jd_data.get_collected_fields()
        missing_fields = jd_data.get_missing_fields()
        
        # Base system prompt
        base_prompt = """You are a professional HR assistant helping create job descriptions. Keep responses SHORT and NATURAL while systematically collecting all required information.

CRITICAL REQUIREMENTS - You MUST obtain these key pieces of information:
1. Job title and role level (e.g., Senior Software Engineer, Marketing Manager)
2. Company name and brief company description
3. Required qualifications and experience level
4. Key responsibilities and duties
5. Required technical skills and technologies
6. Preferred qualifications (nice-to-have skills)
7. Salary range and benefits
8. Work arrangement (remote, hybrid, onsite)
9. Team size and reporting structure
10. Growth opportunities and career development

RESPONSE STYLE:
- Give brief, friendly responses (1-2 sentences max)
- Ask ONE focused question at a time
- Don't repeat back information they just gave you
- Don't confirm every detail - the system captures everything automatically
- Keep the conversation flowing naturally
- Focus on missing information while being conversational

IMPORTANT: Information is extracted automatically - just have a natural conversation and ask good follow-up questions to gather all 10 required pieces."""
        
        # Add current JD status if there's collected information
        if collected_fields:
            status_info = "\n\nCURRENT JD STATUS:"
            status_info += f"\n✅ INFORMATION COLLECTED ({len(collected_fields)}/{len(jd_data.get_all_fields())} fields):"
            for field in collected_fields:
                value = getattr(jd_data, field, None)
                if value:
                    if isinstance(value, list) and value:
                        status_info += f"\n- {field}: {', '.join(value)}"
                    elif isinstance(value, str) and value:
                        display_value = value[:100] + "..." if len(value) > 100 else value
                        status_info += f"\n- {field}: {display_value}"
            
            if missing_fields:
                status_info += f"\n\n❌ STILL MISSING ({len(missing_fields)} fields): {', '.join(missing_fields)}"
                status_info += "\nFocus your questions on gathering this missing information in a natural, conversational way."
            else:
                status_info += "\n\n🎉 ALL INFORMATION COLLECTED! Help them refine and finalize the job description."
            
            base_prompt += status_info
        
        return base_prompt + "\n\nRemember: Be thorough, adaptive, and help them create an attractive, comprehensive JD."
    
    system_prompt = get_dynamic_system_prompt(jd_data)
    
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
    ]
    
    logger.info(f"[BOT] 🎯 System prompt loaded: {len(system_prompt)} characters")
    logger.info("[BOT] 🎯 SYSTEM PROMPT PREVIEW:")
    logger.info(f"[BOT] 🎯 {system_prompt[:200]}...")
    logger.info(f"[BOT] 🎯 ...{system_prompt[-200:]}")
    logger.info("[BOT] 🎯 END SYSTEM PROMPT PREVIEW")

    context = OpenAILLMContext(messages)
    context_aggregator = llm.create_context_aggregator(context)

    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))
    
    # Initialize JD data broadcaster
    jd_broadcaster = JDDataBroadcaster(rtvi, transport)
    jd_update_callback = create_jd_data_callback(jd_broadcaster, jd_data)
    
    # Add callback to JD data for real-time updates
    def sync_callback(field_name: str, field_value: any):
        """Synchronous wrapper for async callback."""
        try:
            # Create task in the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(jd_update_callback(field_name, field_value))
                # Also update the system context with latest JD status
                loop.create_task(update_system_context())
            else:
                logger.warning("[JD_CALLBACK] Event loop not running, skipping async callback")
        except Exception as e:
            logger.error(f"[JD_CALLBACK] Error creating async task: {e}")
    
    async def update_system_context():
        """Update the system context with current JD status."""
        try:
            # Generate updated system prompt
            updated_prompt = get_dynamic_system_prompt(jd_data)
            
            # Update the system message in the context
            if messages and messages[0].get("role") == "system":
                messages[0]["content"] = updated_prompt
                logger.info("[SYSTEM_UPDATE] Updated system prompt with latest JD status")
                logger.debug(f"[SYSTEM_UPDATE] System prompt preview: {updated_prompt[:300]}...")
            else:
                logger.warning("[SYSTEM_UPDATE] Could not find system message to update")
        except Exception as e:
            logger.error(f"[SYSTEM_UPDATE] Error updating system context: {e}")
    
    jd_data.add_update_callback(sync_callback)
    logger.info("[BOT] JD data callback registered successfully")

    # Main pipeline with extraction and broadcasting
    pipeline = Pipeline([
        transport.input(),
        rtvi,
        stt,
        extractor,  # Extract from speech (with improved filtering)
        jd_broadcaster,  # Broadcast JD updates to frontend
        context_aggregator.user(),
        llm,
        tts,
        context_aggregator.assistant(),
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
        logger.info("[BOT] Client connected - Starting JD creation session")
        logger.info(f"[BOT] Initial JD state - Missing fields: {jd_data.get_missing_fields()}")
        logger.info(f"[BOT] Initial JD data values: job_title='{jd_data.job_title}', company_name='{jd_data.company_name}', required_qualifications='{jd_data.required_qualifications}', responsibilities='{jd_data.responsibilities}'")
        
        # Send a brief, natural greeting
        greeting_message = "Hi! I'll help you create a job description. What position are you hiring for?"
        
        greeting_frame = LLMMessagesAppendFrame([
            {
                "role": "assistant",
                "content": greeting_message
            }
        ], run_llm=False)  # Don't trigger LLM, just send the greeting
        
        logger.info("[BOT] 🎯 SENDING JD CREATION GREETING:")
        logger.info(f"[BOT] 🎯 Greeting: {greeting_message}")
        logger.info("[BOT] 🎯 This should ask about JOB TITLE, not experience!")
        await task.queue_frames([greeting_frame])

        # Start background task for JD flow management (with delay)
        logger.info("[BOT] Starting background flow monitor task")
        asyncio.create_task(delayed_flow_monitor(task, flow_manager, messages, context_aggregator))

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("[BOT] Client disconnected")
        logger.info("[JD_FINAL] Job Description creation session ended")
        
        # Log final JD status with detailed breakdown
        collected_fields = jd_data.get_collected_fields()
        missing_fields = jd_data.get_missing_fields()
        completion_status = "COMPLETE" if jd_data.is_complete() else "INCOMPLETE"
        total_fields = len(jd_data.get_all_fields())
        completion_pct = (len(collected_fields) / total_fields) * 100
        
        logger.info(f"[JD_FINAL] 🏁 Session Status: {completion_status} ({completion_pct:.0f}%)")
        logger.info(f"[JD_FINAL] ✅ Collected ({len(collected_fields)}/{total_fields}): {collected_fields}")
        logger.info(f"[JD_FINAL] ❌ Missing ({len(missing_fields)}/{total_fields}): {missing_fields}")
        
        # Log collected data values with explicit value display
        if collected_fields:
            logger.info("[JD_FINAL] 📊 Collected JD Data:")
            for field in collected_fields:
                value = getattr(jd_data, field, None)
                logger.info(f"[JD_FINAL]   • {field}: '{value}' (type: {type(value).__name__})")
        
        # Log guidance attempt summary
        if hasattr(flow_manager, 'guidance_attempts') and flow_manager.guidance_attempts:
            logger.info(f"[JD_FINAL] 🎯 Guidance attempts: {dict(flow_manager.guidance_attempts)}")
        
        # Stop API server
        api_server.stop()
        
        logger.info("[JD_FINAL] 🔄 Cancelling pipeline task...")
        await task.cancel()
        logger.info("[JD_FINAL] ✨ JD creation session cleanup completed")

    runner = PipelineRunner(handle_sigint=False)

    await runner.run(task)


async def delayed_flow_monitor(task, flow_manager, messages, context_aggregator):
    """Start flow monitor after a delay to let initial conversation begin."""
    logger.info("[FLOW_MONITOR] Waiting 120 seconds before starting adaptive guidance")
    await asyncio.sleep(120)  # Wait 2 minutes for natural conversation to start
    logger.info("[FLOW_MONITOR] Starting adaptive JD creation flow monitoring")
    await jd_flow_monitor(task, flow_manager, messages, context_aggregator)


async def jd_flow_monitor(task, flow_manager, messages, context_aggregator):
    """Background task that monitors JD creation progress and provides guidance."""
    logger.info("[JD_FLOW] Starting flow monitor")
    
    try:
        monitor_cycle = 0
        while True:
            await asyncio.sleep(60)  # Check every 60 seconds (more adaptive frequency)
            monitor_cycle += 1
            
            # Check if progress was made on guided field first
            flow_manager.check_field_progress()
            
            # Log current state every cycle with actual values
            collected = flow_manager.jd_data.get_collected_fields()
            missing = flow_manager.jd_data.get_missing_fields()
            total_fields = len(flow_manager.jd_data.get_all_fields())
            completion_pct = (len(collected) / total_fields) * 100
            
            logger.info(f"[JD_FLOW] Cycle #{monitor_cycle} - Progress: {completion_pct:.0f}% ({len(collected)}/{total_fields} fields)")
            logger.info(f"[JD_FLOW] Collected fields: {collected}")
            logger.info(f"[JD_FLOW] Collected values: {[(field, getattr(flow_manager.jd_data, field)) for field in collected]}")
            logger.info(f"[JD_FLOW] Missing: {missing}")
            logger.info(f"[JD_FLOW] Guidance pending: {flow_manager.guidance_pending}")
            
            if flow_manager.should_provide_guidance():
                logger.info(f"[JD_FLOW] Guidance check triggered - attempting to guide conversation")
                guidance = flow_manager.get_guidance_message()
                
                if guidance:
                    missing_fields = flow_manager.jd_data.get_missing_fields()
                    priority_field = missing_fields[0] if missing_fields else "none"
                    attempts = flow_manager.guidance_attempts.get(priority_field, 0)
                    
                    logger.info(f"[JD_FLOW] Generated guidance for field '{priority_field}' (attempt #{attempts + 1}): {guidance}")
                    logger.info(f"[JD_FLOW] All missing fields: {', '.join(missing_fields)}")
                    
                    # Check if we already have recent guidance to avoid duplicates
                    recent_guidance = [msg for msg in messages[-3:] if msg.get("role") == "system" and "guide" in msg.get("content", "").lower()]
                    
                    if not recent_guidance:
                        # Limit message history to prevent bloating
                        if len(messages) > 15:
                            logger.info(f"[JD_FLOW] Message history limit reached ({len(messages)} messages), trimming to 10 recent + system message")
                            # Keep the first system message and recent conversation
                            system_msg = messages[0]
                            recent_messages = messages[-10:]
                            messages.clear()
                            messages.append(system_msg)
                            messages.extend(recent_messages)
                            logger.info(f"[JD_FLOW] Message history trimmed, now {len(messages)} messages")
                        
                        # Add brief guidance to conversation
                        guidance_message = {
                            "role": "system",
                            "content": f"Ask: {guidance} Keep it brief."
                        }
                        messages.append(guidance_message)
                        logger.info(f"[JD_FLOW] Added guidance message to conversation (total messages: {len(messages)})")
                        
                        # Mark guidance attempt
                        flow_manager.mark_guidance_attempt()
                        logger.info(f"[JD_FLOW] Marked guidance attempt for field '{priority_field}' (now {flow_manager.guidance_attempts.get(priority_field, 0)} attempts)")
                        
                        # Trigger LLM to incorporate the guidance with timeout
                        logger.info("[JD_FLOW] Queuing guidance frame to LLM with 15s timeout")
                        try:
                            await asyncio.wait_for(
                                task.queue_frames([
                                    LLMMessagesAppendFrame([guidance_message], run_llm=True)
                                ]),
                                timeout=15.0
                            )
                            logger.info("[JD_FLOW] Successfully queued guidance frame to LLM")
                        except asyncio.TimeoutError:
                            logger.warning("[JD_FLOW] LLM response timeout after 15 seconds, clearing pending status")
                            flow_manager.guidance_pending = False  # Clear pending if timeout
                        except Exception as e:
                            logger.error(f"[JD_FLOW] Error queuing guidance frame: {e}")
                            flow_manager.guidance_pending = False  # Clear pending if error
                    else:
                        logger.info(f"[JD_FLOW] Skipping guidance - found {len(recent_guidance)} recent guidance messages")
                
                else:
                    logger.info("[JD_FLOW] No guidance generated - either complete or no missing priority fields")
                    
                if flow_manager.jd_data.is_complete():
                    logger.info("[JD_FLOW] 🎉 Job Description complete - all information collected! Wrapping up...")
                    final_collected = flow_manager.jd_data.get_collected_fields()
                    logger.info(f"[JD_FLOW] Final collected fields: {final_collected}")
                    logger.info(f"[JD_FLOW] Final JD data: job_title='{flow_manager.jd_data.job_title}', company_name='{flow_manager.jd_data.company_name}', required_qualifications='{flow_manager.jd_data.required_qualifications}', responsibilities='{flow_manager.jd_data.responsibilities}'")
                    
                    completion_message = {
                        "role": "system",
                        "content": "Job description complete! Offer to review or refine anything. Keep it short."
                    }
                    messages.append(completion_message)
                    logger.info("[JD_FLOW] Added completion message, queuing final frame")
                    
                    await task.queue_frames([
                        LLMMessagesAppendFrame([completion_message], run_llm=True)
                    ])
                    logger.info("[JD_FLOW] JD creation flow monitor completed successfully")
                    break
            else:
                logger.info(f"[JD_FLOW] Cycle #{monitor_cycle} - No guidance needed (cooldown: {not flow_manager.should_provide_guidance()})")
                
                # Clear pending status if too much time has passed without progress
                if flow_manager.guidance_pending:
                    import time
                    time_since_guidance = time.time() - flow_manager.last_guidance_time
                    if time_since_guidance > 120:  # 2 minutes
                        logger.warning("[JD_FLOW] Clearing stale guidance pending status after 2 minutes")
                        flow_manager.guidance_pending = False
                    
    except asyncio.CancelledError:
        logger.info("[JD_FLOW] Flow monitor stopped")
    except Exception as e:
        logger.error(f"[JD_FLOW] Monitor error: {e}")


async def bot(runner_args: RunnerArguments):
    """Main bot entry point for the bot starter."""
    logger.info("[BOT] 🚀 BOT ENTRY POINT CALLED!")
    logger.info(f"[BOT] 🚀 Runner args type: {type(runner_args)}")
    
    # Check if this is a SmallWebRTC runner argument
    if isinstance(runner_args, SmallWebRTCRunnerArguments):
        logger.info("[BOT] 🚀 Setting up SmallWebRTC transport")
        transport = SmallWebRTCTransport(
            params=TransportParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
            ),
            webrtc_connection=runner_args.webrtc_connection,
        )
        
        logger.info("[BOT] 🚀 About to call run_bot with transport")
        await run_bot(transport)
        logger.info("[BOT] 🚀 run_bot completed successfully")
    else:
        logger.error(f"[BOT] ❌ Expected SmallWebRTCRunnerArguments, got: {type(runner_args).__name__}")
        raise ValueError("This bot requires SmallWebRTC transport. Run with: python bot.py --transport webrtc")


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
