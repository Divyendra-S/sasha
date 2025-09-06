"use client";

import { Mic, MicOff, Phone, PhoneOff } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useVoiceChat } from "@/hooks/use-voice-chat";
import { useSetAtom } from "jotai";
import { bulkUpdateJDAtom } from "@/stores/jd-atoms";
import { cn } from "@/lib/utils";

export function VoiceChat() {
  const {
    messages,
    isConnecting,
    error,
    connect,
    disconnect,
    startListening,
    stopListening,
    isConnected,
    isListening,
    isProcessing,
  } = useVoiceChat();
  
  const bulkUpdateJD = useSetAtom(bulkUpdateJDAtom);

  const getConnectionStatus = () => {
    if (isConnecting) return { label: "Connecting...", color: "secondary" as const };
    if (error) return { label: "Error", color: "destructive" as const };
    if (isConnected) return { label: "Connected", color: "default" as const };
    return { label: "Disconnected", color: "outline" as const };
  };

  const status = getConnectionStatus();

  return (
    <div className="h-full max-h-[calc(100vh-10rem)] flex flex-col bg-gradient-to-br from-indigo-50 via-white to-white dark:from-slate-900 dark:via-slate-900 dark:to-slate-800">
      {/* Header */}
      <div className="p-6 pb-4 bg-white/70 dark:bg-slate-800/70 backdrop-blur-xl border-b border-indigo-100 dark:border-slate-700 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-3 h-3 rounded-full bg-gradient-to-r from-indigo-500 to-cyan-500 animate-pulse shadow-sm"></div>
              <div className="absolute inset-0 w-3 h-3 rounded-full bg-gradient-to-r from-indigo-500 to-cyan-500 animate-ping opacity-25"></div>
            </div>
            <h2 className="text-xl font-semibold bg-gradient-to-r from-indigo-900 via-purple-900 to-indigo-900 dark:from-white dark:to-slate-200 bg-clip-text text-transparent">
              AI Voice Assistant
            </h2>
          </div>
          <div className="px-3 py-1.5 rounded-full text-xs font-medium bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 border border-indigo-100 dark:border-indigo-800">
            {status.label}
          </div>
        </div>
      </div>
      
      {/* Content */}
      <div className="flex-1 flex flex-col gap-6 p-6">
        {/* Voice Controls */}
        <div className="flex flex-col items-center gap-6">
          {!isConnected ? (
            <div className="flex flex-col items-center gap-6 p-8 bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-lg">
              <div className="relative">
                <button 
                  onClick={connect} 
                  disabled={isConnecting}
                  className="w-20 h-20 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 disabled:from-slate-400 disabled:to-slate-500 shadow-xl hover:shadow-indigo-500/25 transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center group"
                >
                  <Phone className="w-7 h-7 text-white transition-transform group-hover:scale-105" />
                </button>
                {isConnecting && (
                  <div className="absolute inset-0 rounded-full border-2 border-indigo-400 border-t-transparent animate-spin"></div>
                )}
              </div>
              <div className="text-center">
                <span className="text-lg font-semibold text-slate-900 dark:text-slate-100 block">
                  {isConnecting ? "Connecting to AI..." : "Connect to AI"}
                </span>
                <span className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                  Start your voice conversation
                </span>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-6 p-8 bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-lg">
              <div className="flex items-center gap-6">
                <div className="relative">
                  <button 
                    onClick={isListening ? stopListening : startListening}
                    className={`w-20 h-20 rounded-full shadow-xl transition-all duration-300 hover:scale-105 flex items-center justify-center group ${
                      isListening 
                        ? 'bg-rose-600 hover:bg-rose-700 shadow-rose-500/25' 
                        : 'bg-indigo-600 hover:bg-indigo-700 shadow-indigo-500/25'
                    }`}
                  >
                    {isListening ? (
                      <MicOff className="w-7 h-7 text-white transition-transform group-hover:scale-105" />
                    ) : (
                      <Mic className="w-7 h-7 text-white transition-transform group-hover:scale-105" />
                    )}
                  </button>
                  {isListening && (
                    <div className="absolute inset-0 rounded-full border-2 border-rose-300 animate-ping opacity-40"></div>
                  )}
                </div>
                <button 
                  onClick={disconnect}
                  className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 transition-all duration-300 hover:scale-105 flex items-center justify-center shadow-lg border border-slate-200 dark:border-slate-600"
                >
                  <PhoneOff className="w-5 h-5 text-slate-600 dark:text-slate-300" />
                </button>
              </div>
              <div className="text-center">
                <span className="text-lg font-semibold text-slate-900 dark:text-slate-100 block">
                  {isListening ? "AI is listening..." : "Ready to listen"}
                </span>
                <span className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                  {isListening ? "Speak now" : "Click microphone to start"}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="p-6 rounded-2xl bg-rose-50/80 dark:bg-rose-900/20 backdrop-blur-xl border border-rose-200/50 dark:border-rose-800/50 shadow-xl shadow-rose-100/50 dark:shadow-rose-900/20">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-rose-500 to-pink-600 flex items-center justify-center mt-0.5 flex-shrink-0 shadow-lg">
                <span className="text-white text-sm font-bold">!</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-base font-semibold text-rose-800 dark:text-rose-200">AI Connection Error</p>
                <p className="text-sm text-rose-600 dark:text-rose-300 mt-2 leading-relaxed">{error}</p>
                {error.includes('Python server') && (
                  <div className="mt-3 p-3 bg-rose-100/60 dark:bg-rose-800/30 backdrop-blur-sm rounded-xl border border-rose-200/40 dark:border-rose-700/40">
                    <p className="text-sm text-rose-700 dark:text-rose-300">
                      💡 Make sure the voice server is running on port 7860
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Status Indicator */}
        {isConnected && (
          <div className="flex items-center justify-center gap-4 p-4 rounded-xl bg-white/60 dark:bg-slate-800/60 backdrop-blur-xl border border-white/40 dark:border-slate-700/40 shadow-lg shadow-indigo-100/30 dark:shadow-slate-900/30">
            <div className="relative flex items-center gap-3">
              <div className={cn(
                "w-3 h-3 rounded-full transition-all duration-300 shadow-lg",
                isListening && !isProcessing ? "bg-gradient-to-r from-rose-500 to-pink-500 animate-pulse shadow-rose-500/50" : 
                isProcessing ? "bg-gradient-to-r from-amber-500 to-orange-500 animate-bounce shadow-amber-500/50" : 
                "bg-gradient-to-r from-emerald-500 to-teal-500 shadow-emerald-500/50"
              )}>
                {(isListening || isProcessing) && (
                  <div className={cn(
                    "absolute inset-0 rounded-full animate-ping opacity-30",
                    isListening && !isProcessing ? "bg-rose-400" :
                    isProcessing ? "bg-amber-400" :
                    "bg-emerald-400"
                  )} />
                )}
              </div>
              <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                {isProcessing ? "🤖 AI Processing..." : 
                 isListening ? "🎤 Listening..." : 
                 "✨ Ready"}
              </span>
            </div>
          </div>
        )}

        {/* Conversation */}
        {messages.length > 0 && (
          <div className="flex-1 flex flex-col min-h-0">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-600 flex items-center justify-center shadow-lg">
                <span className="text-white text-sm">💬</span>
              </div>
              <h3 className="text-lg font-semibold bg-gradient-to-r from-indigo-900 via-purple-900 to-indigo-900 dark:from-white dark:to-slate-300 bg-clip-text text-transparent">
                AI Conversation
              </h3>
            </div>
            <ScrollArea className="flex-1 rounded-2xl border border-white/30 dark:border-slate-700/30 bg-white/40 dark:bg-slate-800/40 backdrop-blur-xl shadow-xl shadow-indigo-100/20 dark:shadow-slate-900/20">
              <div className="p-6 space-y-4">
                {messages.map((message) => (
                  <div 
                    key={message.id}
                    className={cn(
                      "flex gap-4 animate-in slide-in-from-bottom-2 duration-300",
                      message.role === "user" ? "flex-row-reverse" : "flex-row"
                    )}
                  >
                    <div className={cn(
                      "w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 shadow-lg",
                      message.role === "user" 
                        ? "bg-gradient-to-br from-indigo-500 to-purple-600 text-white" 
                        : "bg-gradient-to-br from-emerald-500 to-teal-600 text-white"
                    )}>
                      {message.role === "user" ? "👤" : "🤖"}
                    </div>
                    <div className={cn(
                      "max-w-[75%] rounded-2xl px-4 py-3 shadow-lg backdrop-blur-sm",
                      message.role === "user" 
                        ? "bg-gradient-to-br from-indigo-500 to-purple-600 text-white" 
                        : "bg-white/90 dark:bg-slate-700/90 border border-white/40 dark:border-slate-600/40 text-slate-900 dark:text-slate-100"
                    )}>
                      <p className="text-sm leading-relaxed">{message.content}</p>
                      <span className={cn(
                        "text-xs mt-2 block opacity-75 font-medium",
                        message.role === "user" 
                          ? "text-indigo-100" 
                          : "text-slate-500 dark:text-slate-400"
                      )}>
                        {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        )}

        {/* Instructions */}
        {!isConnected && !isConnecting && !error && (
          <div className="text-center p-8 bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-lg">
            <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-indigo-600 flex items-center justify-center shadow-lg">
              <Phone className="w-7 h-7 text-white" />
            </div>
            <h3 className="text-xl font-bold bg-gradient-to-r from-indigo-900 via-purple-900 to-indigo-900 dark:from-white dark:to-slate-300 bg-clip-text text-transparent mb-2">
              AI Voice Assistant Ready
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed max-w-sm mx-auto">
              Connect to your AI assistant and start an intelligent voice conversation
            </p>
            <div className="flex items-center justify-center gap-2 mt-4 text-xs text-slate-500 dark:text-slate-400">
              <div className="w-2 h-2 rounded-full bg-indigo-500"></div>
              <span>Powered by AI</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default VoiceChat;