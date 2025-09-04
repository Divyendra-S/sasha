import os
from pipecat.frames.frames import EndFrame, TTSSpeakFrame, LLMRunFrame, LLMMessagesAppendFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from pipecat.services.openai import OpenAILLMService
from pipecat.services.cartesia import CartesiaTTSService
from pipecat.transports.services.daily import DailyTransport, DailyParams
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.services.llm_service import FunctionCallParams

async def main():
    # Create services
    llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"))
    tts = CartesiaTTSService(api_key=os.getenv("CARTESIA_API_KEY"))
    
    transport = DailyTransport(
        room_url="your-room-url",
        token="your-token",
        bot_name="Assistant",
        params=DailyParams(audio_out_enabled=True)
    )

    # Custom Frame Processor using queue_frames
    class CustomProcessor(FrameProcessor):
        async def process_frame(self, frame: Frame, direction: FrameDirection):
            await super().process_frame(frame, direction)
            
            # 4. CUSTOM FRAME PROCESSOR - React to specific frames
            if isinstance(frame, UserStartedSpeakingFrame):
                await task.queue_frames([
                    TTSSpeakFrame("I hear you speaking..."),
                ])
            
            await self.push_frame(frame, direction)

    custom_processor = CustomProcessor()

    # Create pipeline and task
    pipeline = Pipeline([
        transport.input(),
        custom_processor,
        llm,
        tts,
        transport.output(),
    ])
    
    task = PipelineTask(pipeline)

    # 1. EVENT HANDLER - Bot speaks when user joins
    @transport.event_handler("on_first_participant_joined")
    async def on_first_participant_joined(transport, participant):
        await task.queue_frames([
            TTSSpeakFrame("Hello! Welcome to our conversation."),
            LLMRunFrame()  # Start the conversation
        ])

    # 2. FUNCTION CALL HANDLER - End conversation gracefully
    async def end_conversation(params: FunctionCallParams):
        await task.queue_frames([
            TTSSpeakFrame("Thank you for chatting! Have a great day!"),
            EndFrame()  # Terminate pipeline after goodbye
        ])
        await params.result_callback({"status": "conversation_ended"})

    # Register function handler
    llm.register_function("end_conversation", end_conversation)

    # 3. DISCONNECT HANDLER - Immediate cleanup
    @transport.event_handler("on_participant_left")
    async def on_participant_left(transport, participant, reason):
        await task.queue_frames([
            TTSSpeakFrame("Goodbye!"),
            EndFrame()
        ])

    # 5. EXTERNAL TRIGGER - Simulate webhook or timer
    async def external_notification():
        # This could be called from a webhook, timer, or other external event
        await task.queue_frames([
            TTSSpeakFrame("You have a new notification!"),
            LLMMessagesAppendFrame([{
                "role": "system", 
                "content": "A notification just arrived. Mention it to the user."
            }], run_llm=True)
        ])

    # Run the pipeline
    runner = PipelineRunner()
    await runner.run(task)





    What queue_frames() Does
Queues frames for processing in the exact order provided
Processes asynchronously without blocking the calling code
Maintains sequence - frames execute one after another
Integrates with pipeline - frames flow through all processors
Key Usage Locations
Event handlers - Most common usage for responding to transport events
Function call handlers - When LLM calls external functions
Disconnect handlers - Cleanup when users leave
Custom frame processors - Inside your own frame processing logic
External triggers - Webhooks, timers, or other async events
The task object must be accessible in the scope where you call queue_frames(). This is typically passed around or made available through your application's architecture.









import os
from pipecat.frames.frames import EndFrame, TTSSpeakFrame, LLMRunFrame, LLMMessagesAppendFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.cartesia import CartesiaTTSService
from pipecat.transports.services.daily import DailyTransport, DailyParams
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.services.llm_service import FunctionCallParams
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema

async def main():
    # Create services
    llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"))
    tts = CartesiaTTSService(api_key=os.getenv("CARTESIA_API_KEY"))
    
    transport = DailyTransport(
        room_url="your-room-url",
        token="your-token",
        bot_name="Assistant",
        params=DailyParams(audio_out_enabled=True)
    )

    # CUSTOM FRAME PROCESSOR - Multiple use cases
    class SmartProcessor(FrameProcessor):
        def __init__(self):
            super().__init__()
            self.silence_count = 0
            self.conversation_turns = 0

        async def process_frame(self, frame: Frame, direction: FrameDirection):
            await super().process_frame(frame, direction)
            
            # USE CASE 1: Detect user silence and encourage engagement
            if isinstance(frame, UserStoppedSpeakingFrame):
                self.silence_count += 1
                if self.silence_count >= 3:
                    await task.queue_frames([
                        TTSSpeakFrame("I'm here if you need anything else!"),
                    ])
                    self.silence_count = 0
            
            # USE CASE 2: Track conversation flow and offer summaries
            if isinstance(frame, LLMFullResponseEndFrame):
                self.conversation_turns += 1
                if self.conversation_turns % 5 == 0:  # Every 5 exchanges
                    await task.queue_frames([
                        TTSSpeakFrame("Would you like me to summarize our conversation?"),
                        LLMMessagesAppendFrame([{
                            "role": "system",
                            "content": "Ask if the user wants a conversation summary."
                        }], run_llm=True)
                    ])
            
            # USE CASE 3: Error recovery with helpful suggestions
            if isinstance(frame, ErrorFrame):
                await task.queue_frames([
                    TTSSpeakFrame("I encountered an issue. Let me try a different approach."),
                    LLMRunFrame()  # Restart conversation
                ])
            
            await self.push_frame(frame, direction)

    smart_processor = SmartProcessor()

    # Create pipeline and task
    pipeline = Pipeline([
        transport.input(),
        smart_processor,
        llm,
        tts,
        transport.output(),
    ])
    
    task = PipelineTask(pipeline)

    # FUNCTION CALL USE CASES

    # USE CASE 1: Weather with follow-up suggestions
    async def get_weather(params: FunctionCallParams):
        location = params.arguments["location"]
        # Simulate API call
        weather_data = {"temperature": "75°F", "conditions": "sunny"}
        
        await task.queue_frames([
            TTSSpeakFrame(f"The weather in {location} is {weather_data['conditions']} and {weather_data['temperature']}."),
            TTSSpeakFrame("Would you like suggestions for outdoor activities?")
        ])
        await params.result_callback(weather_data)

    # USE CASE 2: Database query with progressive feedback
    async def search_database(params: FunctionCallParams):
        query = params.arguments["query"]
        
        # Provide immediate feedback
        await task.queue_frames([
            TTSSpeakFrame("Searching our database..."),
        ])
        
        # Simulate database search
        results = await simulate_db_search(query)
        
        if results:
            await task.queue_frames([
                TTSSpeakFrame(f"Found {len(results)} results. Here's what I found:"),
            ])
        else:
            await task.queue_frames([
                TTSSpeakFrame("No results found. Let me try a broader search."),
            ])
        
        await params.result_callback(results)

    # USE CASE 3: Multi-step booking process
    async def book_appointment(params: FunctionCallParams):
        date = params.arguments["date"]
        time = params.arguments["time"]
        
        # Step 1: Check availability
        await task.queue_frames([
            TTSSpeakFrame("Checking availability..."),
        ])
        
        # Step 2: Confirm booking
        await task.queue_frames([
            TTSSpeakFrame(f"Great! I've booked your appointment for {date} at {time}."),
            TTSSpeakFrame("You'll receive a confirmation email shortly."),
            LLMMessagesAppendFrame([{
                "role": "system",
                "content": f"Appointment booked for {date} at {time}. Ask if they need anything else."
            }], run_llm=True)
        ])
        
        await params.result_callback({"status": "booked", "date": date, "time": time})

    # USE CASE 4: Smart home control with status updates
    async def control_lights(params: FunctionCallParams):
        action = params.arguments["action"]
        room = params.arguments.get("room", "living room")
        
        await task.queue_frames([
            TTSSpeakFrame(f"Turning {action} the lights in the {room}..."),
        ])
        
        # Simulate device control
        success = await control_smart_device("lights", room, action)
        
        if success:
            await task.queue_frames([
                TTSSpeakFrame(f"Done! The {room} lights are now {action}."),
            ])
        else:
            await task.queue_frames([
                TTSSpeakFrame(f"Sorry, I couldn't control the {room} lights. Please check the connection."),
            ])
        
        await params.result_callback({"success": success, "room": room, "action": action})

    # USE CASE 5: Email composition with confirmation
    async def send_email(params: FunctionCallParams):
        recipient = params.arguments["recipient"]
        subject = params.arguments["subject"]
        
        await task.queue_frames([
            TTSSpeakFrame("Composing your email..."),
        ])
        
        # Draft email
        email_sent = await send_email_api(recipient, subject)
        
        await task.queue_frames([
            TTSSpeakFrame(f"Email sent to {recipient} with subject '{subject}'."),
            TTSSpeakFrame("Is there anything else you'd like me to help with?")
        ])
        
        await params.result_callback({"sent": email_sent, "recipient": recipient})

    # Register all function handlers
    weather_function = FunctionSchema(
        name="get_weather",
        description="Get weather information",
        properties={"location": {"type": "string"}},
        required=["location"]
    )

    search_function = FunctionSchema(
        name="search_database",
        description="Search company database",
        properties={"query": {"type": "string"}},
        required=["query"]
    )

    booking_function = FunctionSchema(
        name="book_appointment",
        description="Book an appointment",
        properties={
            "date": {"type": "string"},
            "time": {"type": "string"}
        },
        required=["date", "time"]
    )

    lights_function = FunctionSchema(
        name="control_lights",
        description="Control smart home lights",
        properties={
            "action": {"type": "string", "enum": ["on", "off"]},
            "room": {"type": "string"}
        },
        required=["action"]
    )

    email_function = FunctionSchema(
        name="send_email",
        description="Send an email",
        properties={
            "recipient": {"type": "string"},
            "subject": {"type": "string"}
        },
        required=["recipient", "subject"]
    )

    tools = ToolsSchema(standard_tools=[
        weather_function, search_function, booking_function, 
        lights_function, email_function
    ])

    # Register all functions
    llm.register_function("get_weather", get_weather)
    llm.register_function("search_database", search_database)
    llm.register_function("book_appointment", book_appointment)
    llm.register_function("control_lights", control_lights)
    llm.register_function("send_email", send_email)

    # EVENT HANDLERS
    @transport.event_handler("on_first_participant_joined")
    async def on_first_participant_joined(transport, participant):
        await task.queue_frames([
            TTSSpeakFrame("Hello! I'm your AI assistant. I can help with weather, appointments, smart home control, and more!"),
            LLMRunFrame()
        ])

    @transport.event_handler("on_participant_left")
    async def on_participant_left(transport, participant, reason):
        await task.queue_frames([
            TTSSpeakFrame("Thanks for chatting! Have a great day!"),
            EndFrame()
        ])

    # Run the pipeline
    runner = PipelineRunner()
    await runner.run(task)

# Helper functions (would be implemented based on your needs)
async def simulate_db_search(query):
    # Simulate database search
    return [{"result": f"Data for {query}"}]

async def control_smart_device(device, room, action):
    # Simulate smart home control
    return True

async def send_email_api(recipient, subject):
    # Simulate email sending
    return True