"use client";

import { PipecatClient } from "@pipecat-ai/client-js";
import { PipecatClientProvider } from "@pipecat-ai/client-react";
import { SmallWebRTCTransport } from "@pipecat-ai/small-webrtc-transport";
import { ReactNode, useMemo } from "react";
import ClientAudio from "@/components/client-audio";

interface PipecatProviderProps {
  children: ReactNode;
}

export function PipecatProvider({ children }: PipecatProviderProps) {
  // Create the client instance only on the client side
  const client = useMemo(() => {
    if (typeof window === 'undefined') {
      return null;
    }
    
    try {
      return new PipecatClient({
        transport: new SmallWebRTCTransport({
          connectionUrl: `${window.location.origin}/api/offer`,
          // Optimize audio for speech
          audioCodec: 'opus',
          waitForICEGathering: true,
          // Reduce connection timeouts for faster feedback
          // Note: rtcConfiguration might not be available in this version
          // connectionTimeout: 15000,
          // reconnectionTimeout: 5000,
        }),
        enableMic: true,
        enableCam: false,
        // Basic configuration - advanced options may not be available in this version
      });
    } catch (error) {
      console.error('Failed to initialize PipecatClient:', error);
      return null;
    }
  }, []);

  if (!client) {
    // Return a loading state or the children without the provider during SSR
    return <>{children}</>;
  }

  return (
    <PipecatClientProvider client={client}>
      {children}
      {/* Audio handling component - handles audio output automatically */}
      <ClientAudio />
    </PipecatClientProvider>
  );
}

export default PipecatProvider;