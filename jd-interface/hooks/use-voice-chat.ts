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
        addMessage("user", data.text.trim());
        updateVoiceStatus({ isProcessing: false });
      }
    };

    const handleBotTranscript = (data: any) => {
      console.log("🤖 Bot transcript:", data);
      if (data.text) {
        addMessage("assistant", data.text);
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

    const handleServerMessage = (data: any) => {
      console.log("📨 Generic server message:", data);
      
      // Check if this is a JD data update message
      if (data?.type === 'jd-data-update' || data?.data?.type === 'jd-data-update') {
        handleJDDataUpdate(data);
        return;
      }
      
      // This is a fallback for any messages we might not be handling specifically
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
  }, [client, updateVoiceStatus, addMessage]);

  // Polling mechanism for JD data as fallback
  useEffect(() => {
    let pollingInterval: NodeJS.Timeout | undefined;
    
    const fetchJDData = async () => {
      try {
        console.log('🔍 Polling JD data from API...');
        const response = await fetch('http://localhost:7861/api/jd-data');
        console.log('🎯 API Response status:', response.status);
        
        if (response.ok) {
          const result = await response.json();
          console.log('📊 Full API result:', result);
          
          if (result.success && result.data) {
            console.log('✅ SUCCESS: Fetched JD data from API:', result.data);
            console.log('🔍 Extracted fields:', result.extractedFields);
            console.log('📊 Current title value:', result.data.title);
            console.log('📊 Current company value:', result.data.company);
            console.log('📊 Current salary value:', result.data.salaryRange);
            
            console.log('🔄 About to call bulkUpdateJD with:', result.data);
            bulkUpdateJD(result.data);
            console.log('✅ bulkUpdateJD call completed');
          } else {
            console.log('⚠️ API response but no data:', result);
          }
        } else {
          console.log('❌ API response failed:', response.status, response.statusText);
        }
      } catch (error) {
        // Don't silently fail - let's see what's happening
        console.log('❌ JD data polling failed:', error);
      }
    };
    
    // For testing: start polling regardless of connection status
    // if (voiceSession.isConnected && !isPollingJDData) {
    if (!isPollingJDData) {
      setIsPollingJDData(true);
      pollingInterval = setInterval(fetchJDData, 1000); // Poll every 1 second for faster updates
      console.log('🔄 Started JD data polling - interval created');
      // Also fetch immediately
      fetchJDData();
    } 
    // Temporarily disable stopping polling for testing
    // else if (!voiceSession.isConnected && isPollingJDData) {
    else if (false) {
      setIsPollingJDData(false);
      console.log('⏹️ Stopped JD data polling');
    }
    
    console.log('📊 Polling status:', {
      isConnected: voiceSession.isConnected,
      isPollingJDData,
      hasInterval: !!pollingInterval
    });
    
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [isPollingJDData, bulkUpdateJD]); // Removed isConnected for testing

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