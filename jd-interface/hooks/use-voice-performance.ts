"use client";

import { useState, useCallback, useRef, useEffect } from "react";

export interface PerformanceMetrics {
  connectionTime: number | null;
  responseTime: number | null;
  averageResponseTime: number;
  totalInteractions: number;
  lastInteractionTime: number | null;
}

export function useVoicePerformance() {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    connectionTime: null,
    responseTime: null,
    averageResponseTime: 0,
    totalInteractions: 0,
    lastInteractionTime: null,
  });

  const connectionStartTime = useRef<number | null>(null);
  const interactionStartTime = useRef<number | null>(null);
  const responseTimes = useRef<number[]>([]);

  const startConnectionTimer = useCallback(() => {
    connectionStartTime.current = performance.now();
  }, []);

  const endConnectionTimer = useCallback(() => {
    if (connectionStartTime.current) {
      const connectionTime = performance.now() - connectionStartTime.current;
      setMetrics(prev => ({ ...prev, connectionTime }));
      console.log(`🔗 Connection established in ${connectionTime.toFixed(2)}ms`);
      connectionStartTime.current = null;
    }
  }, []);

  const startInteractionTimer = useCallback(() => {
    interactionStartTime.current = performance.now();
  }, []);

  const endInteractionTimer = useCallback(() => {
    if (interactionStartTime.current) {
      const responseTime = performance.now() - interactionStartTime.current;
      responseTimes.current.push(responseTime);
      
      const averageResponseTime = responseTimes.current.reduce((a, b) => a + b, 0) / responseTimes.current.length;
      
      setMetrics(prev => ({
        ...prev,
        responseTime,
        averageResponseTime,
        totalInteractions: prev.totalInteractions + 1,
        lastInteractionTime: performance.now(),
      }));
      
      console.log(`⚡ Response received in ${responseTime.toFixed(2)}ms (avg: ${averageResponseTime.toFixed(2)}ms)`);
      
      // Keep only last 10 response times to prevent memory bloat
      if (responseTimes.current.length > 10) {
        responseTimes.current = responseTimes.current.slice(-10);
      }
      
      interactionStartTime.current = null;
    }
  }, []);

  const resetMetrics = useCallback(() => {
    setMetrics({
      connectionTime: null,
      responseTime: null,
      averageResponseTime: 0,
      totalInteractions: 0,
      lastInteractionTime: null,
    });
    responseTimes.current = [];
    connectionStartTime.current = null;
    interactionStartTime.current = null;
  }, []);

  // Performance warnings
  useEffect(() => {
    if (metrics.connectionTime && metrics.connectionTime > 10000) {
      console.warn(`⚠️ Slow connection detected: ${metrics.connectionTime.toFixed(2)}ms`);
    }
    
    if (metrics.averageResponseTime > 5000) {
      console.warn(`⚠️ Slow average response time: ${metrics.averageResponseTime.toFixed(2)}ms`);
    }
  }, [metrics.connectionTime, metrics.averageResponseTime]);

  return {
    metrics,
    startConnectionTimer,
    endConnectionTimer,
    startInteractionTimer,
    endInteractionTimer,
    resetMetrics,
  };
}