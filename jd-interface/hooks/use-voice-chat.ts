"use client";

import { useState, useCallback, useEffect } from "react";
import { usePipecatClient } from "@pipecat-ai/client-react";
import { useAtom, useSetAtom } from "jotai";
import { voiceSessionAtom, updateVoiceStatusAtom, addVoiceMessageAtom, updateJDAtom, bulkUpdateJDAtom } from "@/stores/jd-atoms";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

export function useVoiceChat() {
  const client = usePipecatClient();
  const [voiceSession, setVoiceSession] = useAtom(voiceSessionAtom);
  const updateVoiceStatus = useSetAtom(updateVoiceStatusAtom);
  const addVoiceMessage = useSetAtom(addVoiceMessageAtom);
  const updateJD = useSetAtom(updateJDAtom);
  const bulkUpdateJD = useSetAtom(bulkUpdateJDAtom);
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPollingJDData, setIsPollingJDData] = useState(false);
  const [lastUserTranscript, setLastUserTranscript] = useState<string>("");
  const [lastBotTranscript, setLastBotTranscript] = useState<string>("");

  const addMessage = useCallback((role: "user" | "assistant", content: string) => {
    const newMessage: Message = {
      id: `${Date.now()}-${Math.random()}`,
      role,
      content,
      timestamp: Date.now(),
    };
    setMessages(prev => [...prev, newMessage]);
    addVoiceMessage(content);
  }, [addVoiceMessage]);

  const connect = useCallback(async () => {
    if (isConnecting || voiceSession.isConnected || !client) return;
    
    setIsConnecting(true);
    setError(null);
    
    try {
      // Request microphone permissions first to prevent audio glitches
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        try {
          await navigator.mediaDevices.getUserMedia({ audio: true });
          console.log("🎤 Microphone permission granted");
        } catch (permErr) {
          console.warn("⚠️ Microphone permission denied, but continuing...");
        }
      }

      // Clear any previous processing state
      updateVoiceStatus({
        isProcessing: false,
        isListening: false,
      });

      // Start the bot with proper API request parameters
      await client.startBotAndConnect({
        endpoint: `${window.location.origin}/api/offer`,
        timeout: 30000,
        headers: new Headers({
          'Content-Type': 'application/json',
        }),
      });
      
      updateVoiceStatus({
        isConnected: true,
        isProcessing: false,
      });
      
      console.log("✅ Successfully connected to voice service");
    } catch (err) {
      console.error("❌ Failed to connect to voice service:", err);
      console.error("❌ Error details:", {
        name: err instanceof Error ? err.name : 'Unknown',
        message: err instanceof Error ? err.message : String(err),
        stack: err instanceof Error ? err.stack : undefined
      });
      
      const errorMessage = err instanceof Error ? err.message : "Failed to connect to voice service";
      setError(errorMessage);
      updateVoiceStatus({
        isConnected: false,
        isProcessing: false,
        isListening: false,
      });
    } finally {
      setIsConnecting(false);
    }
  }, [client, isConnecting, voiceSession.isConnected, updateVoiceStatus]);

  const disconnect = useCallback(async () => {
    if (!client) return;
    
    try {
      await client.disconnect();
      updateVoiceStatus({
        isConnected: false,
        isListening: false,
        isProcessing: false,
      });
      console.log("🔌 Disconnected from voice service");
    } catch (err) {
      console.error("❌ Error disconnecting:", err);
    }
  }, [client, updateVoiceStatus]);

  const startListening = useCallback(async () => {
    if (!voiceSession.isConnected) {
      await connect();
      return;
    }


    try {
      // Enable microphone and update listening status
      if (client) {
        await client.enableMic(true);
        updateVoiceStatus({ 
          isListening: true,
          isProcessing: false 
        });
        console.log("🎤 Started listening - microphone enabled");
      }
    } catch (err) {
      console.error("❌ Error starting to listen:", err);
      updateVoiceStatus({ 
        isListening: false, 
        isProcessing: false 
      });
    }
  }, [voiceSession.isConnected, voiceSession.isListening, connect, updateVoiceStatus, client]);

  const stopListening = useCallback(async () => {

    try {
      // Disable microphone and update listening status
      if (client) {
        await client.enableMic(false);
        updateVoiceStatus({ 
          isListening: false,
          isProcessing: false 
        });
        console.log("🛑 Stopped listening - microphone disabled");
      }
    } catch (err) {
      console.error("❌ Error stopping listening:", err);
      updateVoiceStatus({ 
        isListening: false,
        isProcessing: false 
      });
    }
  }, [voiceSession.isListening, updateVoiceStatus, client]);

  // Set up event listeners
  useEffect(() => {
    if (!client) return;

    const handleConnected = () => {
      console.log("🤖 Bot connected");
      updateVoiceStatus({ isConnected: true, isProcessing: false });
    };

    const handleDisconnected = () => {
      console.log("🔌 Bot disconnected");
      updateVoiceStatus({ 
        isConnected: false, 
        isListening: false, 
        isProcessing: false 
      });
    };

    const handleUserTranscript = (data: any) => {
      console.log("📝 User transcript:", data);
      if (data.text && data.text.trim()) {
        const text = data.text.trim();
        // Only add if it's different from the last transcript to avoid duplicates
        if (text !== lastUserTranscript && text.length > 0) {
          console.log("✅ Adding new user message:", text);
          addMessage("user", text);
          setLastUserTranscript(text);
        }
        updateVoiceStatus({ isProcessing: false });
      }
    };

    const handleBotTranscript = (data: any) => {
      console.log("🤖 Bot transcript:", data);
      if (data.text) {
        const text = data.text.trim();
        // Only add if it's different from the last transcript to avoid duplicates
        if (text !== lastBotTranscript && text.length > 0) {
          console.log("✅ Adding new bot message:", text);
          addMessage("assistant", text);
          setLastBotTranscript(text);
        }
        updateVoiceStatus({ isProcessing: false });
      }
    };

    const handleUserStartedSpeaking = () => {
      console.log("🎤 User started speaking");
      updateVoiceStatus({ isProcessing: true });
    };

    const handleUserStoppedSpeaking = () => {
      console.log("🛑 User stopped speaking");
      updateVoiceStatus({ isProcessing: true }); // Processing the speech
    };

    const handleBotStartedSpeaking = () => {
      console.log("🤖 Bot started speaking");
      updateVoiceStatus({ isProcessing: true });
    };

    const handleBotStoppedSpeaking = () => {
      console.log("🤖 Bot stopped speaking");
      updateVoiceStatus({ isProcessing: false });
    };

    const handleJDDataUpdate = (data: any) => {
      console.log("🎯 JD Data Update received:", data);
      
      try {
        // Handle different possible data structures
        let jdData = data;
        if (data?.data?.completeData) {
          jdData = data.data.completeData;
        } else if (data?.completeData) {
          jdData = data.completeData;
        }
        
        if (jdData && typeof jdData === 'object') {
          console.log("✅ Updating JD with:", jdData);
          bulkUpdateJD(jdData);
          
          // Show user feedback
          const fieldName = data?.data?.fieldName || data?.fieldName || 'Unknown';
          const fieldValue = data?.data?.fieldValue || data?.fieldValue || 'Updated';
          console.log(`🔄 JD Field Updated: ${fieldName} = ${fieldValue}`);
        }
      } catch (error) {
        console.error("❌ Error processing JD data update:", error);
      }
    };

    const handleExtractionComplete = async (data: any) => {
      console.log("🎯 Extraction complete event received:", data);
      
      try {
        // Check extraction status first
        const statusResponse = await fetch('http://localhost:7861/api/jd-status');
        if (statusResponse.ok) {
          const statusResult = await statusResponse.json();
          
          if (statusResult.success && statusResult.hasNewExtraction) {
            console.log("✨ New extraction detected, fetching full data...");
            
            // Fetch the full JD data
            const dataResponse = await fetch('http://localhost:7861/api/jd-data');
            if (dataResponse.ok) {
              const dataResult = await dataResponse.json();
              
              if (dataResult.success && dataResult.data) {
                console.log("✅ Event-driven JD update:", dataResult.data);
                bulkUpdateJD(dataResult.data);
                
                // Show user feedback
                const fieldName = data?.data?.fieldName || 'Field';
                console.log(`🔄 JD Field Updated via Event: ${fieldName}`);
              }
            }
          } else {
            console.log("🔄 No new extraction available");
          }
        }
      } catch (error) {
        console.error("❌ Error processing extraction event:", error);
      }
    };

    const handleServerMessage = (data: any) => {
      console.log("📨 Server message received:", JSON.stringify(data, null, 2));
      
      // Handle different possible message wrapping structures
      let actualData = data;
      let messageType = data?.type;
      
      // Check if message is wrapped in a data property
      if (data?.data && typeof data.data === 'object') {
        actualData = data.data;
        messageType = data.data.type || data.type;
        console.log("🔍 Unwrapped message data:", JSON.stringify(actualData, null, 2));
      }
      
      console.log("🏷️ Message type identified:", messageType);
      
      // Check if this is an extraction complete event
      if (messageType === 'extraction-complete') {
        console.log("🎯 Handling extraction-complete event");
        handleExtractionComplete(actualData);
        return;
      }
      
      // Check if this is a JD data update message (legacy support)
      if (messageType === 'jd-data-update') {
        console.log("📊 Handling jd-data-update event");
        handleJDDataUpdate(actualData);
        return;
      }
      
      // Log unhandled message types for debugging
      console.log("🤷 Unhandled server message type:", messageType);
    };

    const handleError = (message: any) => {
      console.error("❌ RTVI Error:", message);
      const errorMsg = message?.data?.message || message?.message || "Connection error";
      setError(errorMsg);
      updateVoiceStatus({
        isConnected: false,
        isListening: false,
        isProcessing: false,
      });
      
      // Clear error after 10 seconds to allow retry
      setTimeout(() => {
        if (errorMsg === message?.data?.message || message?.message || "Connection error") {
          setError(null);
        }
      }, 10000);
    };

    // Add event listeners with correct Pipecat event names
    client.on("connected", handleConnected);
    client.on("disconnected", handleDisconnected);
    client.on("userTranscript", handleUserTranscript);
    client.on("botTranscript", handleBotTranscript);
    client.on("userStartedSpeaking", handleUserStartedSpeaking);
    client.on("userStoppedSpeaking", handleUserStoppedSpeaking);
    client.on("botStartedSpeaking", handleBotStartedSpeaking);
    client.on("botStoppedSpeaking", handleBotStoppedSpeaking);
    // Note: jdDataUpdate events will be handled via serverMessage
    client.on("serverMessage", handleServerMessage); // Fallback handler
    client.on("error", handleError); // Error handler

    return () => {
      client.off("connected", handleConnected);
      client.off("disconnected", handleDisconnected);
      client.off("userTranscript", handleUserTranscript);
      client.off("botTranscript", handleBotTranscript);
      client.off("userStartedSpeaking", handleUserStartedSpeaking);
      client.off("userStoppedSpeaking", handleUserStoppedSpeaking);
      client.off("botStartedSpeaking", handleBotStartedSpeaking);
      client.off("botStoppedSpeaking", handleBotStoppedSpeaking);
      // Note: jdDataUpdate events are handled via serverMessage
      client.off("serverMessage", handleServerMessage);
      client.off("error", handleError);
    };
  }, [client, updateVoiceStatus, addMessage, lastUserTranscript, lastBotTranscript]);

  // Initial JD data fetch and smart polling fallback
  useEffect(() => {
    let pollingInterval: NodeJS.Timeout | undefined;
    let eventsReceived = false;
    let lastExtractionCounter = 0;
    
    const fetchInitialJDData = async () => {
      try {
        console.log('🔄 Fetching initial JD data...');
        const response = await fetch('http://localhost:7861/api/jd-data');
        
        if (response.ok) {
          const result = await response.json();
          
          if (result.success && result.data) {
            console.log('✅ Initial JD data loaded');
            bulkUpdateJD(result.data);
          }
        }
      } catch (error) {
        console.log('⚠️ Initial JD data fetch error:', error);
      }
    };
    
    const checkForUpdates = async () => {
      try {
        const statusResponse = await fetch('http://localhost:7861/api/jd-status');
        if (statusResponse.ok) {
          const statusResult = await statusResponse.json();
          
          // Check if there's new extraction activity
          if (statusResult.success) {
            const currentCounter = statusResult.extractionCounter || 0;
            
            if (statusResult.hasNewExtraction || currentCounter > lastExtractionCounter) {
              console.log('✨ Smart polling detected new extraction, fetching data...');
              
              const dataResponse = await fetch('http://localhost:7861/api/jd-data');
              if (dataResponse.ok) {
                const dataResult = await dataResponse.json();
                
                if (dataResult.success && dataResult.data) {
                  console.log('✅ Smart polling JD update:', dataResult.data);
                  bulkUpdateJD(dataResult.data);
                  lastExtractionCounter = currentCounter;
                }
              }
            }
          }
        }
      } catch (error) {
        // Silently handle polling errors
        if (!(error instanceof Error && error.toString().includes('NetworkError'))) {
          console.log('⚠️ Smart polling error:', error);
        }
      }
    };
    
    // Mark when RTVI events are received (will be called from handleServerMessage)
    const markEventReceived = () => {
      if (!eventsReceived) {
        eventsReceived = true;
        console.log('🎯 RTVI events working, reducing polling frequency');
      }
    };
    
    // Fetch initial data and start smart polling
    if (!isPollingJDData) {
      setIsPollingJDData(true);
      fetchInitialJDData();
      
      // Start smart polling every 5 seconds
      pollingInterval = setInterval(() => {
        if (!eventsReceived) {
          checkForUpdates();
        } else {
          // Reduce polling frequency when events are working
          if (Math.random() < 0.2) { // 20% chance = every ~25 seconds
            checkForUpdates();
          }
        }
      }, 5000);
      
      console.log('🎯 Started smart polling with event detection (5s intervals)');
    }
    
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
        console.log('⏹️ Stopped smart polling');
      }
    };
  }, []); // Run once on mount

  return {
    messages,
    isConnecting,
    error,
    connect,
    disconnect,
    startListening,
    stopListening,
    isConnected: voiceSession.isConnected,
    isListening: voiceSession.isListening,
    isProcessing: voiceSession.isProcessing,
  };
}