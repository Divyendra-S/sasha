"use client";

import { Mic, MicOff, Phone, PhoneOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { useVoiceChat } from "@/hooks/use-voice-chat";
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

  const getConnectionStatus = () => {
    if (isConnecting) return { label: "Connecting...", color: "secondary" as const };
    if (error) return { label: "Error", color: "destructive" as const };
    if (isConnected) return { label: "Connected", color: "default" as const };
    return { label: "Disconnected", color: "outline" as const };
  };

  const status = getConnectionStatus();

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Voice Assistant</CardTitle>
          <Badge variant={status.color}>
            {status.label}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col gap-4">
        {/* Connection Controls */}
        <div className="flex gap-2">
          {!isConnected ? (
            <Button 
              onClick={connect} 
              disabled={isConnecting}
              variant="default"
              className="flex-1"
            >
              <Phone className="w-4 h-4" />
              {isConnecting ? "Connecting..." : "Connect"}
            </Button>
          ) : (
            <>
              <Button 
                onClick={isListening ? stopListening : startListening}
                variant={isListening ? "destructive" : "default"}
                className="flex-1"
              >
                {isListening ? (
                  <>
                    <MicOff className="w-4 h-4" />
                    Stop
                  </>
                ) : (
                  <>
                    <Mic className="w-4 h-4" />
                    Talk
                  </>
                )}
              </Button>
              <Button 
                onClick={disconnect}
                variant="outline"
                size="icon"
              >
                <PhoneOff className="w-4 h-4" />
              </Button>
            </>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20">
            <p className="text-sm text-destructive font-medium">Connection Error</p>
            <p className="text-xs text-destructive/80 mt-1">{error}</p>
            {error.includes('Python server') && (
              <p className="text-xs text-muted-foreground mt-2">
                💡 Make sure the Python voice server is running on port 7860
              </p>
            )}
          </div>
        )}

        {/* Voice Status Indicator */}
        {isConnected && (
          <div className="flex items-center gap-2 p-3 rounded-md bg-muted/50">
            <div className={cn(
              "w-2 h-2 rounded-full",
              isListening && !isProcessing ? "bg-red-500 animate-pulse" : 
              isProcessing ? "bg-orange-500 animate-bounce" : 
              "bg-muted-foreground/50"
            )} />
            <span className="text-sm text-muted-foreground">
              {isProcessing ? "Processing..." : 
               isListening ? "Listening..." : 
               "Ready to listen"}
            </span>
          </div>
        )}

        {/* Conversation Messages */}
        {messages.length > 0 && (
          <div className="flex-1">
            <h3 className="text-sm font-medium mb-2">Conversation</h3>
            <ScrollArea className="h-[300px] rounded-md border p-3">
              <div className="space-y-3">
                {messages.map((message) => (
                  <div 
                    key={message.id}
                    className={cn(
                      "flex",
                      message.role === "user" ? "justify-end" : "justify-start"
                    )}
                  >
                    <div className={cn(
                      "max-w-[80%] rounded-lg px-3 py-2 text-sm",
                      message.role === "user" 
                        ? "bg-primary text-primary-foreground" 
                        : "bg-muted"
                    )}>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs opacity-70 font-medium">
                          {message.role === "user" ? "You" : "Assistant"}
                        </span>
                        <span className="text-xs opacity-50">
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <p>{message.content}</p>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        )}

        {/* Instructions */}
        {!isConnected && !isConnecting && !error && (
          <div className="text-center p-4 text-muted-foreground">
            <p className="text-sm">
              Click &quot;Connect&quot; to start your voice conversation with the AI assistant
            </p>
            <p className="text-xs mt-2 opacity-75">
              Make sure the Python voice server is running
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default VoiceChat;