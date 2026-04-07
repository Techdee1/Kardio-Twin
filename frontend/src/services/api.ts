export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://cardiotwin-jqrct.ondigitalocean.app';

export interface StartSessionRequest {
    session_id: string;
    user_phone?: string;
    caregiver_phone?: string;
    caregiver_name?: string;
    medical_professional_phone?: string;
    medical_professional_name?: string;
}

export interface ComponentScore {
    value: number;
    score: number;
}

export interface SafetyInfo {
    is_safe: boolean;
    escalation: string;
    red_flags: string[];
    safe_next_step: string;
    seek_help_message?: string;
    confidence?: 'low' | 'medium' | 'high';
    reason_drivers?: string[];
}

export interface ActionDriver {
    code: string;
    label: string;
    detail: string;
}

export interface ActionSummary {
    status: string;
    why: string;
    next_step: string;
    if_symptoms: string;
    advice_strength: string;
    confidence_level: 'low' | 'medium' | 'high' | string;
    signal_quality: 'good' | 'ok' | 'poor' | 'unknown' | string;
    signal_confidence: number;
    drivers: ActionDriver[];
}

export interface ScoreResponse {
    status: 'calibrating' | 'retake_requested' | 'scored' | string;
    score?: number;
    zone?: string;
    zone_label?: string;
    zone_emoji?: string;
    alert?: boolean;
    nudge_sent?: boolean;
    source?: string;
    signal_quality?: string;
    signal_confidence?: number;
    safety?: SafetyInfo;
    disclaimer?: string;
    action_summary?: ActionSummary;
    readings_collected?: number;
    readings_needed?: number;
    message?: string;
    components?: {
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

export interface ManualReadingRequest {
    session_id: string;
    bpm: number;
    hrv?: number;
    spo2?: number;
    temperature?: number;
    systolic_bp?: number;
    diastolic_bp?: number;
}

export interface AlertFeedbackRequest {
    session_id: string;
    reading_id?: number;
    alert_type: string;
    feedback: 'helpful' | 'not_helpful' | 'false_alarm';
    comment?: string;
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

    async submitManualReading(data: ManualReadingRequest) {
        const res = await fetch(`${API_BASE_URL}/api/reading/manual`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error('Failed to submit manual reading');
        return res.json();
    },

    async submitAlertFeedback(data: AlertFeedbackRequest) {
        const res = await fetch(`${API_BASE_URL}/api/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error('Failed to submit feedback');
        return res.json();
    },
};
