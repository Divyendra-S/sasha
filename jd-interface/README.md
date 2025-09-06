# JD Creation Interface

A voice-powered job description creation interface built with Next.js 14, Pipecat Voice UI Kit, and real-time editing capabilities.

## Phase 1 Implementation Complete ✅

### Features Implemented

- **Two-Panel Layout**: Voice chat on the left, live JD editor on the right
- **Voice Integration**: Pipecat Voice UI Kit with SmallWebRTC transport
- **Real-time Editor**: Rich text editor with Tiptap and live updates
- **State Management**: Jotai atoms for shared state between voice and editor
- **API Integration**: WebRTC endpoint that proxies to Python server
- **Responsive Design**: Tailwind CSS with modern UI components

### Project Structure

```
jd-interface/
├── app/
│   ├── api/offer/route.ts       # WebRTC endpoint
│   ├── layout.tsx               # Root layout
│   └── page.tsx                 # Main page
├── components/
│   ├── JDCreatorLayout.tsx      # Main two-panel layout
│   ├── VoiceChatPanel.tsx       # Left panel - voice interface
│   └── JDEditorPanel.tsx        # Right panel - JD editor
├── hooks/
│   └── usePipecatVoice.ts       # Pipecat voice management hook
├── stores/
│   └── jd-atoms.ts              # Jotai state atoms
├── .env.local                   # Environment configuration
└── next.config.ts               # Next.js configuration
```

## Getting Started

### Prerequisites

1. **Python Server**: Ensure your Python server is running on port 7860
   ```bash
   cd ../server
   python bot.py
   ```

2. **Environment Variables**: Configure your `.env.local` file with API keys

### Running the Interface

1. **Install Dependencies** (already done):
   ```bash
   npm install
   ```

2. **Start Development Server**:
   ```bash
   npm run dev
   ```

3. **Open Browser**: Navigate to `http://localhost:3000`

### Usage

1. **Connect Voice**: Click the connect button in the left panel
2. **Start Speaking**: Describe your job requirements
3. **See Live Updates**: Watch the job description update in real-time on the right
4. **Edit Manually**: Use the tabbed editor to refine sections
5. **Export**: Use the export buttons to save as PDF or Markdown

## Technical Details

### Voice Integration
- Uses Pipecat Voice UI Kit for voice interface
- SmallWebRTC transport for real-time communication
- Connects to Python server at `localhost:7860/offer`
- Real-time transcription and command processing

### State Management
- Jotai atoms for reactive state management
- Shared state between voice panel and editor
- Real-time synchronization of changes

### Editor Features
- Rich text editing with Tiptap
- Tabbed interface for different JD sections
- Live preview and export capabilities
- Auto-save functionality (ready for implementation)

## Next Steps (Phase 2)

- [ ] Enhanced voice command parsing for JD-specific actions
- [ ] Real-time WebSocket updates from voice commands
- [ ] Template system for different job types
- [ ] Export functionality (PDF, Markdown, JSON)
- [ ] Auto-save and persistence
- [ ] AI-powered suggestions and improvements

## API Endpoints

- `GET/POST /api/offer` - WebRTC offer endpoint (proxies to Python server)
- `GET /api/offer` - Health check for voice service

## Status

✅ **Phase 1 Complete**: Basic setup with voice agent and two-panel interface
🔄 **Ready for Phase 2**: Enhanced voice processing and real-time sync
