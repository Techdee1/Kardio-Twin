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

        // Demo Timeline (1.5s interval):
        // 0-4.5s: Wait (no readings sent - simulating sensor placement, 3 intervals)
        // 4.5-22.5s: NORMAL - hands on sensors, calibration completes after 5 readings (12 total)
        // 24-31.5s: STRESSED - breath hold simulation (5 readings)
        // 33s+: RECOVERY - returning to normal
        
        const count = readingCountRef.current;
        
        // Skip sending readings for first ~4.5 seconds (first 3 intervals @ 1.5s)
        // This simulates waiting for user to place hands on sensors
        if (count < 3) {
            readingCountRef.current++;
            console.log(`[Sensor] Waiting for sensor contact... (${count + 1}/3)`);
            return;
        }
        
        // Adjust count to start from 0 after waiting period
        const adjustedCount = count - 3;
        
        let state: 'healthy' | 'stressed' | 'recovery' = 'healthy';
        
        if (adjustedCount < 12) {
            state = 'healthy'; // Normal baseline (4.5-22.5s), calibration done after 5 readings
        } else if (adjustedCount >= 12 && adjustedCount < 17) {
            state = 'stressed'; // Breath hold stress (24-31.5s)
        } else {
            state = 'recovery'; // Recovery phase (33s+)
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
