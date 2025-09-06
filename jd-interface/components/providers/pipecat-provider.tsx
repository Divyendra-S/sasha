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
    
    return new PipecatClient({
      transport: new SmallWebRTCTransport({
        // Use the simpler connectionUrl format for now
        connectionUrl: `${window.location.origin}/api/offer`,
        // Add audio quality settings
        audioCodec: 'opus',
        waitForICEGathering: true,
      }),
      enableMic: true,
      enableCam: false,
      // Add better audio configuration
      config: {
        // Improve audio quality and reduce latency
        enableMic: true,
        enableCam: false,
      },
    });
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