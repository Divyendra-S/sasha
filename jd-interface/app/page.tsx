import PipecatProvider from '@/components/providers/pipecat-provider';
import VoiceChat from '@/components/voice-chat';
import ClientJobEditor from '@/components/client-job-editor';
import { Provider } from 'jotai';
import { Briefcase } from 'lucide-react';

export default function Home() {
  return (
    <Provider>
      <PipecatProvider>
        <div className="min-h-screen bg-white dark:bg-slate-900">
          {/* Clean Header */}
          <header className="bg-white dark:bg-slate-800 border-b border-gray-200 dark:border-slate-700">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              <div className="flex h-16 items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-2 rounded-lg bg-blue-500 shadow-sm">
                    <Briefcase className="h-5 w-5 text-white" />
                  </div>
                  <div className="flex flex-col">
                    <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
                      JD Creator
                    </h1>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      AI-Powered Job Descriptions
                    </p>
                  </div>
                </div>
                
                {/* Status Badge */}
                <div className="px-3 py-1 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-sm font-medium">
                  AI Ready
                </div>
              </div>
            </div>
          </header>

          {/* Two-Column Layout */}
          <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-[calc(100vh-10rem)]">
              {/* Voice Assistant - Left Side */}
              <div className="order-2 lg:order-1">
                <VoiceChat />
              </div>
              
              {/* Job Description Editor - Right Side */}
              <div className="order-1 lg:order-2">
                <ClientJobEditor />
              </div>
            </div>
          </main>
        </div>
      </PipecatProvider>
    </Provider>
  );
}
