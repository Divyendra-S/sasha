import { useCallback, useEffect, useRef, useState } from "react";
import { useSetAtom } from "jotai";
import { updateVoiceStatusAtom, addVoiceMessageAtom } from "@/stores/jd-atoms";

// Simple voice connection state
interface VoiceState {
  status: 'disconnected' | 'connecting' | 'connected' | 'error';
  isListening: boolean;
}

export const usePipecatVoice = () => {
  const updateVoiceStatus = useSetAtom(updateVoiceStatusAtom);
  const addVoiceMessage = useSetAtom(addVoiceMessageAtom);
  const [state, setState] = useState<VoiceState>({ 
    status: 'disconnected', 
    isListening: false 
  });
  
  const connectionRef = useRef<any>(null);

  const handleConnect = useCallback(async () => {
    try {
      setState({ status: 'connecting', isListening: false });
      updateVoiceStatus({ isConnected: false, isListening: false });

      // Make WebRTC connection to our API endpoint
      const response = await fetch('/api/offer', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: 'offer',
          // Add minimal offer data - the Python server will handle the actual WebRTC setup
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Connection response:', data);
        
        setState({ status: 'connected', isListening: true });
        updateVoiceStatus({ isConnected: true, isListening: true });
        
        // Simulate receiving a welcome message
        setTimeout(() => {
          addVoiceMessage('Connected to voice assistant! Start speaking to describe your job requirements.');
        }, 500);
        
      } else {
        throw new Error(`Connection failed: ${response.status}`);
      }
    } catch (error) {
      console.error("Failed to connect:", error);
      setState({ status: 'error', isListening: false });
      updateVoiceStatus({ isConnected: false, isListening: false });
    }
  }, [updateVoiceStatus, addVoiceMessage]);

  const handleDisconnect = useCallback(() => {
    if (connectionRef.current) {
      // Clean up any active connections
      connectionRef.current = null;
    }
    
    setState({ status: 'disconnected', isListening: false });
    updateVoiceStatus({ isConnected: false, isListening: false });
  }, [updateVoiceStatus]);

  const startListening = useCallback(() => {
    if (state.status === 'connected') {
      setState(prev => ({ ...prev, isListening: true }));
      updateVoiceStatus({ isListening: true });
    }
  }, [state.status, updateVoiceStatus]);

  const stopListening = useCallback(() => {
    setState(prev => ({ ...prev, isListening: false }));
    updateVoiceStatus({ isListening: false });
  }, [updateVoiceStatus]);

  const sendMessage = useCallback((message: string) => {
    if (state.status === 'connected') {
      console.log('Sending message:', message);
      // Here you would send the message to the voice service
      addVoiceMessage(`Sent: ${message}`);
    }
  }, [state.status, addVoiceMessage]);

  return {
    connect: handleConnect,
    disconnect: handleDisconnect,
    startListening,
    stopListening,
    sendMessage,
    state,
  };
};