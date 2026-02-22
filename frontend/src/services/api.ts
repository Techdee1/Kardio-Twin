export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://cardiotwin-jqrct.ondigitalocean.app';

export interface StartSessionRequest {
    session_id: string;
    user_id: string;
}

export interface ComponentScore {
    value: number;
    score: number;
}

export interface ScoreResponse {
    score: number;
    zone: string;
    zone_label: string;
    zone_emoji: string;
    alert?: boolean;
    nudge_sent?: boolean;
    components: {
        heart_rate: ComponentScore;
        hrv: ComponentScore;
        spo2: ComponentScore;
        temperature: ComponentScore;
    };
    baseline?: {
        resting_bpm: number;
        resting_hrv: number;
        normal_spo2: number;
        normal_temp: number;
    };
}

export interface HistoryEntry {
    timestamp: string;
    score: number;
    zone: string;
    components: {
        heart_rate: ComponentScore;
        hrv: ComponentScore;
        spo2: ComponentScore;
        temperature: ComponentScore;
    };
}

export interface PredictionRequest {
    session_id: string;
    days: number;
    scenario?: string;
}

export interface PredictionResponse {
    current_score: number;
    projected_score: number;
    projected_resting_hr_increase_bpm: number;
    current_risk_category: string;
    projected_risk_category: string;
    disclaimer: string;
    scenario_note?: string;
}

export interface NudgeResponse {
    message: string;
    zone: string;
    zone_label: string;
    phone: string | null;
}

export const api = {
    async startSession(data: StartSessionRequest) {
        const res = await fetch(`${API_BASE_URL}/api/session/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error('Failed to start session');
        return res.json();
    },

    async getScore(sessionId: string): Promise<any> {
        const res = await fetch(`${API_BASE_URL}/api/score/${sessionId}`);
        if (!res.ok) throw new Error('Failed to fetch score');
        const data = await res.json();
        if (data.status === 'error' || data.error) {
            throw new Error(data.message || 'Invalid score data format');
        }
        return data;
    },

    async getHistory(sessionId: string): Promise<HistoryEntry[]> {
        const res = await fetch(`${API_BASE_URL}/api/history/${sessionId}`);
        if (!res.ok) throw new Error('Failed to fetch history');
        const data = await res.json();
        if (data.status === 'error' || data.error || !Array.isArray(data)) {
            throw new Error(data.message || 'Invalid history data format');
        }
        return data;
    },

    async getPrediction(data: PredictionRequest): Promise<PredictionResponse> {
        const res = await fetch(`${API_BASE_URL}/api/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error('Failed to fetch prediction');
        return res.json();
    },

    async getNudge(sessionId: string): Promise<NudgeResponse> {
        const res = await fetch(`${API_BASE_URL}/api/nudge/${sessionId}`);
        if (!res.ok) throw new Error('Failed to fetch nudge');
        return res.json();
    },

    async submitReading(data: {
        session_id: string;
        bpm: number;
        hrv: number;
        spo2: number;
        temperature: number;
    }) {
        const res = await fetch(`${API_BASE_URL}/api/reading`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error('Failed to submit reading');
        return res.json();
    },
};
