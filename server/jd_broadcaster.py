"""
Job Description Data Broadcasting System

This module provides a frame processor that broadcasts JD data updates
to the frontend via RTVI messages.
"""

import asyncio
import json
from typing import Optional
from loguru import logger

from pipecat.frames.frames import Frame
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection


class JDDataUpdateFrame(Frame):
    """Custom frame for JD data updates."""
    
    def __init__(self, field_name: str, field_value: any, complete_data: dict):
        super().__init__()
        self.field_name = field_name
        self.field_value = field_value
        self.complete_data = complete_data


class JDDataBroadcaster(FrameProcessor):
    """
    Frame processor that broadcasts JD data updates via RTVI messages.
    
    This processor receives JD data update notifications and converts them
    into RTVI messages that can be sent to the frontend.
    """
    
    def __init__(self, rtvi_processor, transport=None):
        super().__init__()
        self.rtvi_processor = rtvi_processor
        self.transport = transport
        logger.info("[JD_BROADCASTER] Initialized JD data broadcaster")
    
    async def broadcast_jd_update(self, field_name: str, field_value: any, complete_data: dict):
        """Broadcast a JD data update via RTVI."""
        try:
            logger.info(f"[JD_BROADCASTER] Broadcasting update for field '{field_name}': {field_value}")
            
            # Create custom RTVI message
            rtvi_message = {
                "type": "jd-data-update",
                "data": {
                    "fieldName": field_name,
                    "fieldValue": field_value,
                    "completeData": complete_data,
                    "timestamp": asyncio.get_event_loop().time() * 1000
                }
            }
            
            # Try multiple approaches to send the message
            message_sent = False
            
            # Approach 1: Try RTVI send_server_message if available
            if self.rtvi_processor and hasattr(self.rtvi_processor, 'send_server_message'):
                try:
                    await self.rtvi_processor.send_server_message(rtvi_message)
                    logger.info(f"[JD_BROADCASTER] ✅ Sent RTVI update for '{field_name}'")
                    message_sent = True
                    
                    # Also send extraction-complete event via RTVI
                    extraction_event = {
                        "type": "extraction-complete",
                        "data": {
                            "hasNewExtraction": True,
                            "fieldName": field_name,
                            "timestamp": asyncio.get_event_loop().time() * 1000
                        }
                    }
                    await self.rtvi_processor.send_server_message(extraction_event)
                    logger.info(f"[JD_BROADCASTER] 🎯 Sent extraction event via RTVI")
                    
                except Exception as e:
                    logger.warning(f"[JD_BROADCASTER] RTVI send_server_message failed: {e}")
            
            # Approach 2: Try transport send if available
            if not message_sent and self.transport and hasattr(self.transport, 'send_message'):
                try:
                    await self.transport.send_message(json.dumps(rtvi_message))
                    logger.info(f"[JD_BROADCASTER] ✅ Sent transport message for '{field_name}'")
                    message_sent = True
                except Exception as e:
                    logger.warning(f"[JD_BROADCASTER] Transport send_message failed: {e}")
            
            # Approach 3: Try to send via WebSocket directly using transport's connection
            if not message_sent and self.transport and hasattr(self.transport, '_websocket'):
                try:
                    import websockets
                    if hasattr(self.transport, '_websocket') and self.transport._websocket:
                        ws_message = json.dumps({
                            "type": "serverMessage",
                            "data": rtvi_message
                        })
                        await self.transport._websocket.send(ws_message)
                        logger.info(f"[JD_BROADCASTER] ✅ Sent WebSocket message for '{field_name}'")
                        message_sent = True
                except Exception as e:
                    logger.warning(f"[JD_BROADCASTER] WebSocket send failed: {e}")
            
            # Approach 4: Log to console as fallback and create frame
            if not message_sent:
                logger.info(f"[JD_BROADCASTER] 📡 Broadcasting JD Update (console fallback):")
                logger.info(f"[JD_BROADCASTER] 🎯 Type: jd-data-update")
                logger.info(f"[JD_BROADCASTER] 📊 Field: {field_name}")
                logger.info(f"[JD_BROADCASTER] 💾 Value: {field_value}")
                logger.info(f"[JD_BROADCASTER] 🔄 Complete Data: {json.dumps(complete_data, indent=2)}")
                
                # Create custom frame for pipeline processing
                update_frame = JDDataUpdateFrame(field_name, field_value, complete_data)
                await self.push_frame(update_frame, FrameDirection.DOWNSTREAM)
                logger.info(f"[JD_BROADCASTER] ✅ Sent custom frame for '{field_name}'")
                
                # Send extraction notification event
                extraction_event = {
                    "type": "extraction-complete",
                    "data": {
                        "hasNewExtraction": True,
                        "fieldName": field_name,
                        "timestamp": asyncio.get_event_loop().time() * 1000
                    }
                }
                
                # Try to send extraction event via multiple channels
                if self.rtvi_processor and hasattr(self.rtvi_processor, 'send_server_message'):
                    try:
                        await self.rtvi_processor.send_server_message(extraction_event)
                        logger.info(f"[JD_BROADCASTER] 🎯 Sent extraction event via RTVI")
                    except Exception as e:
                        logger.warning(f"[JD_BROADCASTER] RTVI extraction event failed: {e}")
                
                # Also try to write to a shared file that frontend can poll
                try:
                    import tempfile
                    import os
                    temp_dir = tempfile.gettempdir()
                    jd_file = os.path.join(temp_dir, 'jd_data_updates.json')
                    with open(jd_file, 'w') as f:
                        json.dump({
                            "timestamp": asyncio.get_event_loop().time() * 1000,
                            "field": field_name,
                            "value": field_value,
                            "complete_data": complete_data
                        }, f)
                    logger.info(f"[JD_BROADCASTER] 💾 Wrote update to temp file: {jd_file}")
                except Exception as e:
                    logger.warning(f"[JD_BROADCASTER] Failed to write temp file: {e}")
            
        except Exception as e:
            logger.error(f"[JD_BROADCASTER] ❌ Error broadcasting JD update: {e}")
    
    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        """Process frames - currently just passes them through."""
        await super().process_frame(frame, direction)
        
        # Handle our custom JD update frames
        if isinstance(frame, JDDataUpdateFrame):
            logger.info(f"[JD_BROADCASTER] Processing JD update frame for field: {frame.field_name}")
            # Frame has been processed, continue with normal flow
        
        # Always pass frame through
        await self.push_frame(frame, direction)


def create_jd_data_callback(broadcaster: JDDataBroadcaster, jd_data):
    """Create a callback function for JD data updates."""
    
    async def on_jd_update(field_name: str, field_value: any):
        """Callback function that gets called when JD data is updated."""
        try:
            logger.info(f"[JD_CALLBACK] JD data updated: {field_name} = {field_value}")
            
            # Get complete data in frontend format
            complete_data = jd_data.to_frontend_format()
            
            # Broadcast the update
            await broadcaster.broadcast_jd_update(field_name, field_value, complete_data)
            
        except Exception as e:
            logger.error(f"[JD_CALLBACK] Error in JD update callback: {e}")
    
    return on_jd_update