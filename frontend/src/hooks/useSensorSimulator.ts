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

// Simulates realistic biometric variations for demo
function generateReading(baseState: 'healthy' | 'stressed' | 'recovery' = 'healthy'): SimulatedReading {
    const baseValues = {
        healthy: { bpm: 68, hrv: 55, spo2: 98, temp: 36.5 },
        stressed: { bpm: 95, hrv: 25, spo2: 94, temp: 37.4 }, // Breath hold stress
        recovery: { bpm: 75, hrv: 45, spo2: 97, temp: 36.8 },
    };

    const base = baseValues[baseState];
    
    // Add realistic noise for actual readings
    return {
        bpm: Math.round(base.bpm + (Math.random() - 0.5) * 6),
        hrv: Math.round(base.hrv + (Math.random() - 0.5) * 8),
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

        // Demo Timeline (2s interval):
        // 0-14s: Wait (no readings sent - simulating no sensor contact)
        // 15-24s (readings 0-4): NORMAL - hands placed on sensors
        // 25-38s (readings 5-11): NORMAL - continue baseline  
        // 40-48s (readings 12-16): STRESSED - breath hold simulation
        // 50s+ (readings 17+): RECOVERY - returning to normal
        
        const count = readingCountRef.current;
        
        // Skip sending readings for first 15 seconds (first 7-8 intervals)
        // This simulates waiting for user to place hands on sensors
        if (count < 7) {
            readingCountRef.current++;
            console.log(`[Sensor] Waiting for sensor contact... (${count + 1}/7)`);
            return;
        }
        
        // Adjust count to start from 0 after waiting period
        const adjustedCount = count - 7;
        
        let state: 'healthy' | 'stressed' | 'recovery' = 'healthy';
        
        if (adjustedCount < 12) {
            state = 'healthy'; // Normal baseline (15-38s)
        } else if (adjustedCount >= 12 && adjustedCount < 17) {
            state = 'stressed'; // Breath hold stress (40-48s)
        } else {
            state = 'recovery'; // Recovery phase (50s+)
        }

        const reading = generateReading(state);
        
        try {
            const response = await api.submitReading({
                session_id: sessionId,
                ...reading
            });
            
            readingCountRef.current++;
            
            const stateLabels = {
                healthy: '✅ NORMAL',
                stressed: '⚠️ STRESSED',
                recovery: '🔄 RECOVERY'
            };
            
            console.log(`[Sensor] Reading #${adjustedCount + 1} [${stateLabels[state]}]:`, reading, response.status);
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
