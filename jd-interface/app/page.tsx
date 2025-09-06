import PipecatProvider from '@/components/providers/pipecat-provider';
import VoiceChat from '@/components/voice-chat';
import ClientJobEditor from '@/components/client-job-editor';
import { Provider } from 'jotai';
import { Briefcase } from 'lucide-react';

export default function Home() {
  return (
    <Provider>
      <PipecatProvider>
        <div className="min-h-screen bg-gradient-to-br from-background to-muted/20">
          {/* Header */}
          <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container flex h-16 items-center gap-4 px-6">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                  <Briefcase className="h-4 w-4" />
                </div>
                <div>
                  <h1 className="text-lg font-semibold">JD Creator</h1>
                  <p className="text-xs text-muted-foreground">AI-Powered Job Descriptions</p>
                </div>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="container mx-auto p-6">
            <div className="grid h-[calc(100vh-8rem)] gap-6 lg:grid-cols-5">
              {/* Voice Chat Panel - 2/5 width */}
              <div className="lg:col-span-2">
                <VoiceChat />
              </div> 
              {/* Job Description Editor Panel - 3/5 width */}
              <div className="lg:col-span-3">
                <ClientJobEditor />
              </div>
            </div>
          </main>
        </div>
      </PipecatProvider>
    </Provider>
  );
}
