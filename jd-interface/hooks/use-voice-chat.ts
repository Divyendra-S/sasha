"use client";

import { useState, useCallback, useEffect } from "react";
import { usePipecatClient } from "@pipecat-ai/client-react";
import { useAtom, useSetAtom } from "jotai";
import { voiceSessionAtom, updateVoiceStatusAtom, addVoiceMessageAtom } from "@/stores/jd-atoms";

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
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
        updateVoiceStatus({ isListening: true });
        console.log("🎤 Started listening - microphone enabled");
      }
    } catch (err) {
      console.error("❌ Error starting to listen:", err);
      updateVoiceStatus({ isListening: false });
    }
  }, [voiceSession.isConnected, connect, updateVoiceStatus, client]);

  const stopListening = useCallback(async () => {
    try {
      // Disable microphone and update listening status
      if (client) {
        await client.enableMic(false);
        updateVoiceStatus({ isListening: false });
        console.log("🛑 Stopped listening - microphone disabled");
      }
    } catch (err) {
      console.error("❌ Error stopping listening:", err);
      updateVoiceStatus({ isListening: false });
    }
  }, [updateVoiceStatus, client]);

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
      if (data.text) {
        addMessage("user", data.text);
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

    const handleServerMessage = (data: any) => {
      console.log("📨 Generic server message:", data);
      // This is a fallback for any messages we might not be handling specifically
    };

    const handleError = (message: any) => {
      console.error("❌ RTVI Error:", message);
      setError(message?.data?.message || message?.message || "Connection error");
      updateVoiceStatus({
        isConnected: false,
        isListening: false,
        isProcessing: false,
      });
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
      client.off("serverMessage", handleServerMessage);
      client.off("error", handleError);
    };
  }, [client, updateVoiceStatus, addMessage]);

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