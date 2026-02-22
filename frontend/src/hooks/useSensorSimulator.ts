import { useEffect, useRef, useCallback } from 'react';
import { api } from '../services/api';

interface SensorSimulatorOptions {
    sessionId: string | null;
    enabled: boolean;
    intervalMs?: number;
    onReading?: (reading: SimulatedReading, response: any) => void;
}

interface SimulatedReading {
    bpm: number;
    hrv: number;
    spo2: number;
    temperature: number;
}

// Simulates realistic biometric variations
function generateReading(baseState: 'healthy' | 'stressed' | 'critical' = 'healthy'): SimulatedReading {
    const baseValues = {
        healthy: { bpm: 68, hrv: 55, spo2: 98, temp: 36.5 },
        stressed: { bpm: 85, hrv: 35, spo2: 96, temp: 37.2 },
        critical: { bpm: 110, hrv: 20, spo2: 92, temp: 38.5 },
    };

    const base = baseValues[baseState];
    
    // Add realistic noise
    return {
        bpm: Math.round(base.bpm + (Math.random() - 0.5) * 8),
        hrv: Math.round(base.hrv + (Math.random() - 0.5) * 10),
        spo2: Math.round(Math.min(100, base.spo2 + (Math.random() - 0.5) * 2)),
        temperature: parseFloat((base.temp + (Math.random() - 0.5) * 0.3).toFixed(1)),
    };
}

export function useSensorSimulator({ 
    sessionId, 
    enabled, 
    intervalMs = 2000,
    onReading 
}: SensorSimulatorOptions) {
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const readingCountRef = useRef(0);

    const sendReading = useCallback(async () => {
        if (!sessionId) return;

        // Simulate different health states for demo purposes
        // First 20 readings: healthy calibration
        // Then vary based on demo scenario
        let state: 'healthy' | 'stressed' | 'critical' = 'healthy';
        const count = readingCountRef.current;
        
        if (count > 25 && count < 35) {
            state = 'stressed'; // Simulate some stress
        } else if (count >= 35 && count < 40) {
            state = 'healthy'; // Recovery
        }

        const reading = generateReading(state);
        
        try {
            const response = await api.submitReading({
                session_id: sessionId,
                ...reading
            });
            
            readingCountRef.current++;
            
            console.log(`[Sensor] Reading #${readingCountRef.current} sent:`, reading, response.status);
            console.log(`[Sensor] Full response:`, JSON.stringify(response));
            
            if (onReading) {
                console.log(`[Sensor] Calling onReading callback`);
                onReading(reading, response);
            }
        } catch (error) {
            console.error('[Sensor] Failed to send reading:', error);
        }
    }, [sessionId, onReading]);

    useEffect(() => {
        if (enabled && sessionId) {
            // Reset counter on new session
            readingCountRef.current = 0;
            
            // Start sending readings
            console.log(`[Sensor] Starting simulator for session: ${sessionId}`);
            sendReading(); // Send first reading immediately
            
            intervalRef.current = setInterval(sendReading, intervalMs);
        }

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
                intervalRef.current = null;
                console.log('[Sensor] Simulator stopped');
            }
        };
    }, [enabled, sessionId, intervalMs, sendReading]);

    return {
        isSimulating: enabled && !!sessionId,
        readingCount: readingCountRef.current,
    };
}

export { generateReading };
