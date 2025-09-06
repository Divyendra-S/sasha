"use client";

import { PipecatClientAudio } from "@pipecat-ai/client-react";
import { useEffect, useState } from "react";

export function ClientAudio() {
  const [isMounted, setIsMounted] = useState(false);
  const [audioContext, setAudioContext] = useState<AudioContext | null>(null);
  const [isAudioReady, setIsAudioReady] = useState(false);

  useEffect(() => {
    setIsMounted(true);
    
    // Initialize audio context for better audio handling
    const initAudioContext = async () => {
      if (typeof window !== 'undefined' && (window.AudioContext || (window as any).webkitAudioContext)) { // eslint-disable-line @typescript-eslint/no-explicit-any
        const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext; // eslint-disable-line @typescript-eslint/no-explicit-any
        const context = new AudioContextClass({
          sampleRate: 16000, // Optimize for speech
          latencyHint: 'interactive' // Low latency for real-time
        });
        setAudioContext(context);
        
        // Resume audio context if it's suspended (required by some browsers)
        const resumeAudio = async () => {
          try {
            if (context.state === 'suspended') {
              await context.resume();
              console.log('🔊 Audio context resumed successfully');
              setIsAudioReady(true);
            } else if (context.state === 'running') {
              console.log('🔊 Audio context already running');
              setIsAudioReady(true);
            }
            
            // Remove listeners after successful resume
            document.removeEventListener('click', resumeAudio);
            document.removeEventListener('touchstart', resumeAudio);
            document.removeEventListener('keydown', resumeAudio);
          } catch (error) {
            console.error('❌ Failed to resume audio context:', error);
          }
        };
        
        // Add multiple event listeners for user interaction
        document.addEventListener('click', resumeAudio, { once: true });
        document.addEventListener('touchstart', resumeAudio, { once: true });
        document.addEventListener('keydown', resumeAudio, { once: true });
        
        // Try to resume immediately if possible
        if (context.state !== 'suspended') {
          setIsAudioReady(true);
        }
      }
    };

    initAudioContext();
    
    return () => {
      if (audioContext && audioContext.state !== 'closed') {
        audioContext.close().catch(console.error);
      }
    };
  }, []);

  useEffect(() => {
    // Log audio readiness for debugging
    if (isAudioReady) {
      console.log('🔊 Audio system ready for voice chat');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAudioReady]); // audioContext is only used for cleanup and doesn't need to be in deps

  if (!isMounted) {
    return null;
  }

  return (
    <>
      <PipecatClientAudio />
      {/* Audio readiness indicator (hidden, for debugging) */}
      {process.env.NODE_ENV === 'development' && (
        <div 
          style={{ 
            position: 'fixed', 
            top: '10px', 
            right: '10px', 
            fontSize: '12px', 
            color: isAudioReady ? 'green' : 'orange',
            zIndex: 9999,
            backgroundColor: 'rgba(0,0,0,0.8)',
            padding: '4px 8px',
            borderRadius: '4px'
          }}
        >
          Audio: {isAudioReady ? 'Ready' : 'Initializing...'}
        </div>
      )}
    </>
  );
}

export default ClientAudio;