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
    <div className="h-full max-h-[calc(100vh-10rem)] flex flex-col bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="p-4 bg-slate-50 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className={cn(
                "w-3 h-3 rounded-full transition-colors",
                isConnected ? "bg-green-500 animate-pulse" : "bg-slate-400"
              )}></div>
            </div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
              Voice Assistant
            </h2>
          </div>
          <div className={cn(
            "px-3 py-1.5 rounded-full text-xs font-medium border",
            status.color === "default" && "bg-green-50 text-green-700 border-green-200 dark:bg-green-900/30 dark:text-green-300 dark:border-green-800",
            status.color === "secondary" && "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800",
            status.color === "destructive" && "bg-red-50 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-300 dark:border-red-800",
            status.color === "outline" && "bg-slate-50 text-slate-700 border-slate-200 dark:bg-slate-900/30 dark:text-slate-300 dark:border-slate-800"
          )}>
            {status.label}
          </div>
        </div>
      </div>
      
      {/* Content */}
      <div className="flex-1 flex flex-col gap-4 p-4 overflow-hidden">
        {/* Voice Controls */}
        <div className="flex flex-col items-center gap-4">
          {!isConnected ? (
            <div className="flex flex-col items-center gap-4 p-6 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
              <div className="relative">
                <button 
                  onClick={connect} 
                  disabled={isConnecting}
                  className="w-16 h-16 rounded-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 transition-all duration-200 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center group shadow-lg"
                >
                  <Phone className="w-6 h-6 text-white" />
                </button>
                {isConnecting && (
                  <div className="absolute inset-0 rounded-full border-2 border-indigo-400 border-t-transparent animate-spin"></div>
                )}
              </div>
              <div className="text-center">
                <span className="text-base font-medium text-slate-900 dark:text-slate-100 block">
                  {isConnecting ? "Connecting..." : "Connect"}
                </span>
                <span className="text-sm text-slate-500 dark:text-slate-400">
                  {isConnecting ? "Please wait" : "Start conversation"}
                </span>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-4 p-6 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
              <div className="flex items-center gap-4">
                <div className="relative">
                  <button 
                    onClick={isListening ? stopListening : startListening}
                    className={cn(
                      "w-16 h-16 rounded-full shadow-lg transition-all duration-200 hover:scale-105 flex items-center justify-center group",
                      isListening 
                        ? "bg-red-600 hover:bg-red-700" 
                        : "bg-blue-600 hover:bg-blue-700"
                    )}
                  >
                    {isListening ? (
                      <MicOff className="w-6 h-6 text-white" />
                    ) : (
                      <Mic className="w-6 h-6 text-white" />
                    )}
                  </button>
                  {isListening && (
                    <div className="absolute inset-0 rounded-full border-2 border-rose-300 animate-ping opacity-40"></div>
                  )}
                </div>
                <button 
                  onClick={disconnect}
                  className="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 transition-all duration-200 hover:scale-105 flex items-center justify-center border border-slate-200 dark:border-slate-600"
                >
                  <PhoneOff className="w-4 h-4 text-slate-600 dark:text-slate-300" />
                </button>
              </div>
              <div className="text-center">
                <span className="text-base font-medium text-slate-900 dark:text-slate-100 block">
                  {isListening ? "Listening..." : "Ready"}
                </span>
                <span className="text-sm text-slate-500 dark:text-slate-400">
                  {isListening ? "Speak now" : "Click mic to start"}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-red-500 flex items-center justify-center mt-0.5 flex-shrink-0">
                <span className="text-white text-xs font-bold">!</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-red-800 dark:text-red-200">Connection Error</p>
                <p className="text-sm text-red-600 dark:text-red-300 mt-1">{error}</p>
                {error.includes('Python server') && (
                  <div className="mt-2 p-2 bg-red-100 dark:bg-red-800/30 rounded border border-red-200 dark:border-red-700">
                    <p className="text-xs text-red-700 dark:text-red-300">
                      Make sure the voice server is running on port 7860
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Status Indicator */}
        {isConnected && (
          <div className="flex items-center justify-center gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
            <div className="relative flex items-center gap-3">
              <div className={cn(
                "w-2 h-2 rounded-full transition-all duration-300",
                isListening && !isProcessing ? "bg-red-500 animate-pulse" : 
                isProcessing ? "bg-amber-500 animate-bounce" : 
                "bg-green-500"
              )}>
              </div>
              <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                {isProcessing ? "Processing..." : 
                 isListening ? "Listening..." : 
                 "Ready"}
              </span>
            </div>
          </div>
        )}

        {/* Conversation */}
        {messages.length > 0 && (
          <div className="flex-1 flex flex-col min-h-0">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-6 h-6 rounded-lg bg-blue-600 flex items-center justify-center">
                <span className="text-white text-xs">💬</span>
              </div>
              <h3 className="text-base font-medium text-slate-900 dark:text-white">
                Conversation
              </h3>
            </div>
            <ScrollArea className="flex-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 min-h-0">
              <div className="p-4 space-y-3">
                {messages.map((message) => (
                  <div 
                    key={message.id}
                    className={cn(
                      "flex gap-3 animate-in slide-in-from-bottom-2 duration-300",
                      message.role === "user" ? "flex-row-reverse" : "flex-row"
                    )}
                  >
                    <div className={cn(
                      "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0",
                      message.role === "user" 
                        ? "bg-blue-600 text-white" 
                        : "bg-green-600 text-white"
                    )}>
                      {message.role === "user" ? "U" : "A"}
                    </div>
                    <div className={cn(
                      "max-w-[75%] rounded-lg px-3 py-2",
                      message.role === "user" 
                        ? "bg-blue-600 text-white" 
                        : "bg-slate-100 dark:bg-slate-700 text-slate-900 dark:text-slate-100 border border-slate-200 dark:border-slate-600"
                    )}>
                      <p className="text-sm leading-normal">{message.content}</p>
                      <span className={cn(
                        "text-xs mt-1 block opacity-75",
                        message.role === "user" 
                          ? "text-blue-100" 
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
          <div className="text-center p-6 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
            <div className="w-12 h-12 mx-auto mb-4 rounded-lg bg-blue-600 flex items-center justify-center">
              <Phone className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-base font-medium text-slate-900 dark:text-white mb-2">
              Voice Assistant Ready
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-xs mx-auto">
              Connect to start voice conversation
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default VoiceChat;