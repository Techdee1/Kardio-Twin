import { useEffect, useState, useRef } from "react";
import { api } from "../services/api";
import { useLanguage } from "../i18n/LanguageContext";

const ZONE_COLORS: Record<string, string> = {
    GREEN: "#22C55E",
    YELLOW: "#FACC15",
    ORANGE: "#F97316",
    RED: "#EF4444",
};

export default function DemoPage() {
    const [score, setScore] = useState(0);
    const [displayScore, setDisplayScore] = useState(0);
    const [zone, setZone] = useState("GREEN");
    const [alert, setAlert] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [calibrating, setCalibrating] = useState(true);
    const [progress, setProgress] = useState(0);
    const sensorInterval = useRef<ReturnType<typeof setInterval> | null>(null);
    const { t } = useLanguage();

    const ZONE_LABELS: Record<string, string> = {
        GREEN: t('demo.thriving'),
        YELLOW: t('demo.mildStrain'),
        ORANGE: t('demo.elevatedRisk'),
        RED: t('demo.criticalStrain'),
    };

    // Initialize session on mount
    useEffect(() => {
        const initSession = async () => {
            const newSessionId = `demo-${Date.now()}`;
            try {
                await api.startSession({ session_id: newSessionId, user_id: 'demo-user' });
                setSessionId(newSessionId);
                console.log('[Demo] Session started:', newSessionId);
            } catch (err) {
                console.error('[Demo] Failed to start session:', err);
            }
        };
        initSession();
    }, []);

    // Sensor simulator - sends mock biometric data
    useEffect(() => {
        if (!sessionId) return;

        const sendReading = async () => {
            // Generate realistic biometric data
            const bpm = 68 + Math.floor(Math.random() * 15);
            const hrv = 45 + Math.floor(Math.random() * 20);
            const spo2 = 96 + Math.floor(Math.random() * 4);
            const temperature = 36.4 + Math.random() * 0.6;

            try {
                await api.submitReading({
                    session_id: sessionId,
                    bpm,
                    hrv,
                    spo2,
                    temperature: parseFloat(temperature.toFixed(1))
                });
            } catch (err) {
                console.error('[Demo] Reading failed:', err);
            }
        };

        sendReading(); // Initial reading
        sensorInterval.current = setInterval(sendReading, 2000);

        return () => {
            if (sensorInterval.current) {
                clearInterval(sensorInterval.current);
            }
        };
    }, [sessionId]);

    // Count up animation
    useEffect(() => {
        if (displayScore < score) {
            const timer = setTimeout(() => {
                setDisplayScore((prev) => Math.min(prev + 1, score));
            }, 20);
            return () => clearTimeout(timer);
        }
    }, [displayScore, score]);

    // Poll API every 2 seconds
    useEffect(() => {
        if (!sessionId) return;

        const poll = async () => {
            try {
                const data = await api.getScore(sessionId);
                if (data.status === 'calibrating') {
                    setCalibrating(true);
                    setProgress((data.readings_collected || 0) / (data.readings_needed || 15));
                } else if (data.score !== undefined) {
                    setCalibrating(false);
                    setScore(Math.round(data.score));
                    setZone(data.zone || "GREEN");
                    setAlert(data.alert || false);
                }
            } catch (err) {
                console.log("Polling error:", err);
            }
        };
        poll();
        const interval = setInterval(poll, 2000);
        return () => clearInterval(interval);
    }, [sessionId]);

    const color = ZONE_COLORS[zone] || "#22C55E";
    const label = ZONE_LABELS[zone] || t('demo.thriving');

    return (
        <div
            className="min-h-screen flex flex-col items-center justify-center px-4"
            style={{ backgroundColor: "#0F172A" }}
        >
            {/* Alert Banner */}
            {alert && (
                <div
                    className="w-full text-center py-3 sm:py-4 text-white text-lg sm:text-2xl font-bold animate-pulse"
                    style={{ backgroundColor: "#EF4444" }}
                >
                    {t('demo.alert')}
                </div>
            )}

            {/* Logo */}
            <h1 className="text-white text-2xl sm:text-3xl font-bold mb-2 tracking-widest uppercase">
                CardioTwin AI
            </h1>
            <p className="text-slate-400 text-base sm:text-lg mb-8 sm:mb-12 text-center">
                {t('demo.subtitle')}
            </p>

            {calibrating ? (
                /* Calibration View */
                <div className="flex flex-col items-center">
                    <div
                        className="rounded-full flex flex-col items-center justify-center animate-pulse w-[220px] h-[220px] sm:w-[320px] sm:h-[320px]"
                        style={{
                            border: `10px solid #60a5fa`,
                            boxShadow: `0 0 60px #60a5fa, 0 0 120px #60a5fa40`,
                        }}
                    >
                        <span className="text-3xl sm:text-4xl text-blue-400 font-bold mb-2">
                            {Math.round(progress * 100)}%
                        </span>
                        <span className="text-slate-400 text-base sm:text-lg">Calibrating...</span>
                    </div>
                    <p className="text-slate-500 text-sm mt-6 sm:mt-8 max-w-xs text-center">
                        Establishing your personal baseline. Please remain still.
                    </p>
                </div>
            ) : (
                /* Score View */
                <>
                    {/* Score Circle */}
                    <div
                        className="rounded-full flex flex-col items-center justify-center w-[220px] h-[220px] sm:w-[320px] sm:h-[320px]"
                        style={{
                            border: `10px solid ${color}`,
                            boxShadow: `0 0 60px ${color}, 0 0 120px ${color}40`,
                            transition: "all 0.3s ease-in-out",
                        }}
                    >
                        <span
                            className="font-bold text-[64px] sm:text-[96px]"
                            style={{ color: color, lineHeight: 1 }}
                        >
                            {displayScore}
                        </span>
                        <span className="text-slate-400 text-lg sm:text-xl mt-2">{t('demo.scoreLabel')}</span>
                    </div>

                    {/* Zone Label */}
                    <div
                        className="mt-6 sm:mt-8 px-6 sm:px-8 py-2.5 sm:py-3 rounded-full text-lg sm:text-2xl font-bold"
                        style={{
                            backgroundColor: `${color}20`,
                            color: color,
                            border: `2px solid ${color}`,
                            transition: "all 0.3s ease-in-out",
                        }}
                    >
                        {zone === "GREEN" && "🟢"}
                        {zone === "YELLOW" && "🟡"}
                        {zone === "ORANGE" && "🟠"}
                        {zone === "RED" && "🔴"} {label}
                    </div>
                </>
            )}

            {/* Footer */}
            <p className="text-slate-600 text-xs sm:text-sm mt-10 sm:mt-16 text-center">
                {t('demo.disclaimer')}
            </p>
        </div>
    );
}
