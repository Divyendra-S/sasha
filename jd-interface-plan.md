# JD Creation Interface Implementation Plan

## Overview

Create a two-panel interface for Job Description creation with voice integration using **Pipecat Voice UI Kit**, **functional React patterns**, and **existing Python server integration**.

## Architecture

### Two-Panel Layout

- **Left Panel:** Voice Chat Interface (Pipecat Bot Conversation)
- **Right Panel:** **Live-Updating Job Description** (Real-time modifications)
- **Real-time sync:** Bot conversation directly modifies JD content as user speaks
- **Live Preview:** User sees JD changes instantly during voice interaction

## Technology Stack

### Frontend Components

- **Next.js 14+** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **React Hook Form** for form management
- **Jotai** for state management (functional approach)

### Voice Integration

- **Pipecat Voice UI Kit** (`@pipecat-ai/voice-ui-kit`)
- **Pipecat Client React** (`@pipecat-ai/client-react`)
- **Small WebRTC Transport** (`@pipecat-ai/small-webrtc-transport`)
- **Existing Python Server** integration

### Live JD Editor

- **Tiptap** or **React Quill** for rich text editing with real-time updates
- **Live synchronization** with bot conversation
- **Instant visual feedback** as bot processes user requests
- **Auto-save** functionality for persistence

## Implementation Plan

### Phase 1: Basic UI Structure (Week 1)

#### 1.1 Layout Setup

```jsx
// components/jd-creator/JDCreatorLayout.tsx
<div className="flex h-screen">
  <VoiceChatPanel className="w-1/2" />
  <JDEditorPanel className="w-1/2" />
</div>
```

#### 1.2 Voice Chat Panel

```jsx
// components/jd-creator/VoiceChatPanel.tsx
- Audio visualization
- Connection status indicator
- Voice activity detection
- Chat history display
- Microphone controls
```

#### 1.3 JD Editor Panel

```jsx
// components/jd-creator/JDEditorPanel.tsx
- Rich text editor
- Template selector
- Live preview mode
- Export functionality
```

### Phase 2: Pipecat Integration (Week 2)

#### 2.1 Pipecat Voice UI Kit Setup

**Installation:**

```bash
npm i @pipecat-ai/voice-ui-kit @pipecat-ai/client-js @pipecat-ai/client-react
npm i @pipecat-ai/small-webrtc-transport
```

**Functional Hook-based Setup:**

```typescript
// hooks/usePipecatVoice.ts
import { usePipecat } from "@pipecat-ai/client-react";
import { SmallWebRTCTransport } from "@pipecat-ai/small-webrtc-transport";

export const usePipecatVoice = () => {
  const { connect, disconnect, state } = usePipecat({
    transport: new SmallWebRTCTransport({
      webrtcUrl: "/api/offer",
    }),
  });

  return { connect, disconnect, state };
};
```

**Python Server Integration:**

- Your existing Python server handles bot logic
- Client connects via WebRTC offer endpoint
- Real-time communication through WebRTC transport

**API Routes:**

- `POST /api/offer` - WebRTC offer endpoint (connects to Python server)
- `GET /api/status` - Connection status

#### 2.2 Voice UI Kit Components Integration

**Using Pre-built Components:**

```typescript
// components/VoiceChatPanel.tsx
import {
  VoiceVisualizer,
  ConnectButton,
  ControlBar,
  ThemeProvider,
} from "@pipecat-ai/voice-ui-kit";

const VoiceChatPanel = () => {
  const { connect, disconnect, state } = usePipecatVoice();

  return (
    <ThemeProvider>
      <div className="voice-panel">
        <ConnectButton onConnect={connect} />
        <VoiceVisualizer state={state} />
        <ControlBar onDisconnect={disconnect} />
      </div>
    </ThemeProvider>
  );
};
```

#### 2.3 Voice Command Processing

**Functional Voice Processing:**

```typescript
// hooks/useVoiceCommands.ts
import { useCallback } from "react";

interface VoiceCommand {
  type: "update" | "insert" | "delete" | "format";
  target: "title" | "description" | "requirements" | "benefits";
  content: string;
  position?: number;
}

export const useVoiceCommands = () => {
  const processCommand = useCallback((message: string): VoiceCommand => {
    // AI-powered command parsing
    return parseCommand(message);
  }, []);

  return { processCommand };
};
```

### Phase 3: Real-time Editor Integration (Week 3)

#### 3.1 State Management

**Jotai Atoms:**

```typescript
// stores/jd-creator-atoms.ts
import { atom } from 'jotai';

interface JobDescription {
  title: string;
  company: string;
  description: string;
  requirements: string[];
  benefits: string[];
}

interface VoiceSession {
  isConnected: boolean;
  isListening: boolean;
  transcript: string[];
}

export const jobDescriptionAtom = atom<JobDescription>({
  title: '',
  company: '',
  description: '',
  requirements: [],
  benefits: [],
});

export const voiceSessionAtom = atom<VoiceSession>({
  isConnected: false,
  isListening: false,
  transcript: [],
});

// Derived atoms
export const updateJDAtom = atom(
  null,
  (get, set, updates: Partial<JobDescription>) => {
    const current = get(jobDescriptionAtom);
    set(jobDescriptionAtom, { ...current, ...updates });
  }
);

export const addVoiceMessageAtom = atom(
  null,
  (get, set, message: string) => {
    const current = get(voiceSessionAtom);
    set(voiceSessionAtom, {
      ...current,
      transcript: [...current.transcript, message],
    });
  }
);
```

#### 3.2 Real-time Synchronization

**Functional Voice-to-Editor Sync:**

```typescript
// hooks/useVoiceSync.ts
import { useCallback } from "react";
import { useSetAtom } from "jotai";
import { updateJDAtom } from "../stores/jd-creator-atoms";

export const useVoiceSync = () => {
  const updateJD = useSetAtom(updateJDAtom);

  const handleVoiceCommand = useCallback(
    (command: VoiceCommand) => {
      switch (command.type) {
        case "update":
          updateJD({ [command.target]: command.content });
          break;
        case "insert":
          insertAtPosition(command.target, command.content, command.position);
          break;
        // ... other command types
      }
    },
    [updateJD]
  );

  return { handleVoiceCommand };
};
```

#### 3.3 Auto-save & WebSocket Updates

**Functional Auto-save Hook:**

```typescript
// hooks/useAutoSave.ts
import { useEffect } from "react";
import { useDebouncedCallback } from "use-debounce";

export const useAutoSave = (data: JobDescription) => {
  const debouncedSave = useDebouncedCallback(async (jdData: JobDescription) => {
    await saveJD(jdData);
  }, 1000);

  useEffect(() => {
    if (data) {
      debouncedSave(data);
    }
  }, [data, debouncedSave]);

  return { debouncedSave };
};
```

### Phase 4: Advanced Features (Week 4)

#### 4.1 Template System

**Functional Template Hook:**

```typescript
// hooks/useJDTemplates.ts
import { useState, useCallback } from "react";

const templates = {
  software_engineer: {
    title: "Software Engineer",
    sections: ["overview", "requirements", "responsibilities", "benefits"],
  },
  devops_engineer: {
    title: "DevOps Engineer",
    sections: ["overview", "technical_requirements", "responsibilities"],
  },
} as const;

export const useJDTemplates = () => {
  const [selectedTemplate, setSelectedTemplate] = useState<
    keyof typeof templates | null
  >(null);

  const selectTemplate = useCallback((templateKey: keyof typeof templates) => {
    setSelectedTemplate(templateKey);
  }, []);

  return {
    templates,
    selectedTemplate,
    selectTemplate,
    currentTemplate: selectedTemplate ? templates[selectedTemplate] : null,
  };
};
```

#### 4.2 AI-Powered Enhancements

**Functional AI Suggestions Hook:**

```typescript
// hooks/useAISuggestions.ts
import { useState, useCallback } from "react";

export const useAISuggestions = () => {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const generateSuggestions = useCallback(
    async (context: string, voiceInput: string) => {
      setIsLoading(true);
      try {
        const prompt = `
        Based on the current JD context: ${context}
        And voice input: ${voiceInput}
        Suggest improvements or additions.
      `;

        const result = await callLLM(prompt);
        setSuggestions(result);
      } catch (error) {
        console.error("Failed to generate suggestions:", error);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  return { suggestions, generateSuggestions, isLoading };
};
```

#### 4.3 Export & Validation

**Functional Export Hook:**

```typescript
// hooks/useJDExport.ts
import { useCallback } from "react";

type ExportFormat = "markdown" | "pdf" | "json";

export const useJDExport = () => {
  const exportJD = useCallback(
    async (jd: JobDescription, format: ExportFormat) => {
      switch (format) {
        case "markdown":
          return convertToMarkdown(jd);
        case "pdf":
          return await generatePDF(jd);
        case "json":
          return JSON.stringify(jd, null, 2);
        default:
          throw new Error(`Unsupported format: ${format}`);
      }
    },
    []
  );

  return { exportJD };
};
```

## API Endpoints

### Core Endpoints

```typescript
// API Routes Structure (integrates with existing Python server)
/api/
├── offer               # POST - WebRTC offer (connects to Python server)
├── status             # GET - Connection status
├── jd/
│   ├── create         # POST - Create new JD
│   ├── [id]           # GET/PUT - Retrieve/Update JD
│   ├── templates      # GET - Available templates
│   └── export/[format] # POST - Export JD (pdf/md/json)
└── ai/
    ├── suggestions    # POST - Get AI suggestions
    └── validate       # POST - Validate JD content
```

### Pipecat Integration Endpoints

**WebRTC Offer Endpoint (connects to Python server):**

```typescript
// pages/api/offer.ts
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  try {
    // Forward WebRTC offer to your Python server
    const response = await fetch("http://localhost:7860/offer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req.body),
    });

    const data = await response.json();
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: "Failed to connect to Python server" });
  }
}
```

## WebRTC Configuration with SmallWebRTC

### Client-Side Setup

```typescript
// lib/webrtc-config.ts
const webrtcConfig = {
  iceServers: [
    { urls: "stun:stun.l.google.com:19302" },
    {
      urls: "turn:your-turn-server.com:3478",
      username: "user",
      credential: "pass",
    },
  ],
  audio: {
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true,
  },
};
```

### Functional SmallWebRTC Integration

```typescript
// hooks/useSmallWebRTC.ts
import { useEffect, useRef } from "react";
import { SmallWebRTCTransport } from "@pipecat-ai/small-webrtc-transport";

export const useSmallWebRTC = (webrtcUrl: string) => {
  const transportRef = useRef<SmallWebRTCTransport | null>(null);

  useEffect(() => {
    transportRef.current = new SmallWebRTCTransport({ webrtcUrl });

    return () => {
      transportRef.current?.disconnect();
    };
  }, [webrtcUrl]);

  return transportRef.current;
};
```

## Component Architecture

### Voice Chat Panel Components

```
VoiceChatPanel/
├── AudioVisualizer.tsx      # Voice activity visualization
├── ConnectionStatus.tsx     # WebRTC connection indicator
├── ChatHistory.tsx          # Voice interaction history
├── VoiceControls.tsx        # Mic on/off, settings
└── TranscriptDisplay.tsx    # Real-time transcription
```

### JD Editor Panel Components

```
JDEditorPanel/
├── RichTextEditor.tsx       # Main editor (Tiptap/Quill)
├── TemplateSelector.tsx     # JD template chooser
├── PreviewMode.tsx          # Live preview toggle
├── SectionEditor.tsx        # Individual section editing
└── ExportControls.tsx       # Export options
```

## State Flow

### Voice Command Flow

```
Voice Input → Pipecat Processing → Command Parsing → State Update → Editor Refresh
```

### Auto-save Flow

```
Editor Changes → Debounced Save → API Call → Database Update → Success Feedback
```

## Error Handling

### Functional Error Handling

```typescript
// hooks/useErrorHandling.ts
import { useCallback } from "react";

export const useErrorHandling = () => {
  const handleConnectionError = useCallback((error: Error) => {
    // Retry logic
    if (error.code === "WEBRTC_FAILED") {
      setTimeout(() => reconnect(), 2000);
    }

    // Fallback to text input
    if (error.code === "VOICE_UNAVAILABLE") {
      enableTextMode();
    }
  }, []);

  return { handleConnectionError };
};
```

### Functional Voice Error Handling

```typescript
// hooks/useVoiceErrorHandling.ts
import { useCallback } from "react";

interface VoiceError {
  type: "NO_SPEECH" | "AUDIO_CAPTURE" | "CONNECTION_FAILED";
  message: string;
}

export const useVoiceErrorHandling = () => {
  const handleVoiceError = useCallback((error: VoiceError) => {
    switch (error.type) {
      case "NO_SPEECH":
        showPrompt("Please speak into the microphone");
        break;
      case "AUDIO_CAPTURE":
        showError("Microphone access denied");
        break;
      case "CONNECTION_FAILED":
        showError("Failed to connect to voice service");
        break;
    }
  }, []);

  return { handleVoiceError };
};
```

## Testing Strategy

### Unit Tests

- Voice command parsing
- State management
- Editor synchronization
- Template system

### Integration Tests

- WebRTC connection
- Pipecat communication
- Real-time updates
- Auto-save functionality

### E2E Tests

- Complete JD creation flow
- Voice-to-text accuracy
- Export functionality
- Error recovery

## Deployment Considerations

### Environment Variables

```env
# Python Server Configuration
PYTHON_SERVER_URL=http://localhost:7860

# API Keys (handled by Python server)
OPENAI_API_KEY=your_openai_key
DEEPGRAM_API_KEY=your_deepgram_key
CARTESIA_API_KEY=your_cartesia_key

# Database & Cache
DATABASE_URL=your_mongodb_url
REDIS_URL=your_redis_url

# WebRTC Configuration
WEBRTC_TURN_SERVER=your_turn_server
```

### Performance Optimization

- WebRTC connection pooling
- Audio stream buffering
- Editor debouncing
- Template caching

### Security

- API key protection
- WebRTC encryption
- Input sanitization
- Rate limiting

## Success Metrics

### Technical Metrics

- WebRTC connection success rate (>95%)
- Voice command accuracy (>90%)
- Real-time sync latency (<100ms)
- Auto-save reliability (>99%)

### User Experience Metrics

- Time to create JD (target: <5 minutes)
- Voice command adoption rate
- Template usage rate
- Export success rate

## Future Enhancements

### Phase 2 Features

- Multi-language support
- Custom voice models
- Advanced AI suggestions
- Collaborative editing

### Phase 3 Features

- Mobile app integration
- Offline mode support
- Advanced analytics
- Integration with HR systems
