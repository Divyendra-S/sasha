"use client";

import { PipecatClientAudio } from "@pipecat-ai/client-react";
import { useEffect, useState } from "react";

export function ClientAudio() {
  const [isMounted, setIsMounted] = useState(false);
  const [audioContext, setAudioContext] = useState<AudioContext | null>(null);

  useEffect(() => {
    setIsMounted(true);
    
    // Initialize audio context for better audio handling
    const initAudioContext = () => {
      if (typeof window !== 'undefined' && window.AudioContext) {
        const context = new window.AudioContext();
        setAudioContext(context);
        
        // Resume audio context if it's suspended (required by some browsers)
        if (context.state === 'suspended') {
          const resumeAudio = () => {
            context.resume().then(() => {
              console.log('🔊 Audio context resumed');
              document.removeEventListener('click', resumeAudio);
              document.removeEventListener('touchstart', resumeAudio);
            });
          };
          
          document.addEventListener('click', resumeAudio);
          document.addEventListener('touchstart', resumeAudio);
        }
      }
    };

    initAudioContext();
    
    return () => {
      if (audioContext && audioContext.state !== 'closed') {
        audioContext.close();
      }
    };
  }, []);

  if (!isMounted) {
    return null;
  }

  return <PipecatClientAudio />;
}

export default ClientAudio;