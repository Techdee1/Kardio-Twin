import { useState, useEffect, useCallback, useMemo, useRef, Suspense } from 'react';
import { Activity, Bell, BrainCircuit, Sparkles, Globe, Check } from 'lucide-react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import Sidebar from '../components/dashboard/Sidebar';
import NudgePanel from '../components/dashboard/NudgePanel';
import ProjectionPanel from '../components/dashboard/ProjectionPanel';
import HistoryChart from '../components/dashboard/HistoryChart';
import ManualInputPanel, { type ManualSubmittedVitals } from '../components/dashboard/ManualInputPanel';
import { api } from '../services/api';
import type { ActionSummary, NudgeResponse, ScoreResponse } from '../services/api';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment } from '@react-three/drei';
import { HealthAvatar } from '../components/HealthAvatar';
import { useLanguage, LANGUAGE_OPTIONS } from '../i18n/LanguageContext';
import { useSensorSimulator } from '../hooks/useSensorSimulator';
import {
    DATA_SOURCE_MODE_OPTIONS,
    DATA_SOURCE_MODE,
    type DataSourceMode,
    getModeDefaults,
    getStoredDataSourceMode,
    setStoredDataSourceMode,
} from '../config/dataSource';

export interface Vitals {
    heartRate: number;
    hrv: number;
    spO2: number;
    skinTemp: number;
    score: number;
    trend: string;
}

function formatSourceLabel(source?: string): string {
    if (!source) return 'UNKNOWN';
    return source.replace(/_/g, ' ').trim().toUpperCase();
}

const SOURCE_SWITCH_DEBOUNCE_MS = 1500;

const DEFAULT_ACTION_SUMMARY: ActionSummary = {
    status: 'Monitoring',
    why: 'Waiting for enough data to provide guidance.',
    next_step: 'Continue monitoring and submit a fresh reading.',
    if_symptoms: 'If chest pain or shortness of breath occurs, seek help now.',
    advice_strength: 'cautious',
    confidence_level: 'low',
    signal_quality: 'unknown',
    signal_confidence: 0,
    drivers: [],
};

function getActionSummaryFromResponse(response: Partial<ScoreResponse>): ActionSummary {
    if (response.action_summary) {
        return {
            ...DEFAULT_ACTION_SUMMARY,
            ...response.action_summary,
            drivers: response.action_summary.drivers || [],
        };
    }

    if (response.status === 'calibrating') {
        return {
            ...DEFAULT_ACTION_SUMMARY,
            status: 'Calibrating',
            why: 'Building baseline from recent manual readings.',
            next_step: 'Submit another reading to continue calibration.',
            advice_strength: 'calibration',
            confidence_level: 'low',
            signal_quality: response.signal_quality || 'unknown',
            signal_confidence: response.signal_confidence || 0,
        };
    }

    if (response.status === 'retake_requested') {
        return {
            ...DEFAULT_ACTION_SUMMARY,
            status: 'Retake needed',
            why: response.message || 'Reading quality is too low for reliable guidance.',
            next_step: 'Ensure proper sensor contact, stay still, and retake now.',
            advice_strength: 'retake_only',
            confidence_level: 'low',
            signal_quality: response.signal_quality || 'poor',
            signal_confidence: response.signal_confidence || 0,
            drivers: [
                {
                    code: 'signal_quality_low',
                    label: 'Low signal quality',
                    detail: 'The sensor reading confidence is low.',
                },
            ],
        };
    }

    return DEFAULT_ACTION_SUMMARY;
}

export default function DashboardPage() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const sessionId = searchParams.get('session_id');
    const { lang, setLang, t } = useLanguage();

    const initialMode = getStoredDataSourceMode() ?? DATA_SOURCE_MODE;
    const [selectedMode, setSelectedMode] = useState<DataSourceMode>(initialMode);
    const modeFlags = useMemo(() => getModeDefaults(selectedMode), [selectedMode]);

    const defaultView: 'overview' | 'projection' | 'history' | 'manual' | 'settings' =
        initialMode === 'manual' ? 'manual' : 'overview';

    const [activeView, setActiveView] = useState<'overview' | 'projection' | 'history' | 'manual' | 'settings'>(defaultView);

    const defaultVitals: Vitals = {
        heartRate: 0,
        hrv: 0,
        spO2: 100,
        skinTemp: 36.5,
        score: 0,
        trend: 'Stable'
    };

    const [liveVitals, setLiveVitals] = useState<Vitals>(defaultVitals);
    const [nudge, setNudge] = useState<NudgeResponse | null>(null);
    const [showNudge, setShowNudge] = useState(false);
    const [isLoadingNudge, setIsLoadingNudge] = useState(false);
    const [activeSource, setActiveSource] = useState<string>(formatSourceLabel(initialMode));
    const sourceDebounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    // Initial load check
    useEffect(() => {
        if (!sessionId) {
            navigate('/');
        }
    }, [sessionId, navigate]);

    useEffect(() => {
        if (!modeFlags.enableManualEntry && activeView === 'manual') {
            setActiveView('overview');
        }
    }, [activeView, modeFlags.enableManualEntry]);

    const requestSourceSwitch = useCallback((nextSource?: string) => {
        const normalizedSource = formatSourceLabel(nextSource);
        if (normalizedSource === activeSource) {
            return;
        }

        if (sourceDebounceTimerRef.current) {
            clearTimeout(sourceDebounceTimerRef.current);
        }

        sourceDebounceTimerRef.current = setTimeout(() => {
            setActiveSource(normalizedSource);
            sourceDebounceTimerRef.current = null;
        }, SOURCE_SWITCH_DEBOUNCE_MS);
    }, [activeSource]);

    const toggleMode = useCallback(() => {
        const currentIndex = DATA_SOURCE_MODE_OPTIONS.indexOf(selectedMode);
        const nextIndex = (currentIndex + 1) % DATA_SOURCE_MODE_OPTIONS.length;
        const nextMode = DATA_SOURCE_MODE_OPTIONS[nextIndex];

        setSelectedMode(nextMode);
        setStoredDataSourceMode(nextMode);
        requestSourceSwitch(nextMode);
    }, [requestSourceSwitch, selectedMode]);

    useEffect(() => {
        return () => {
            if (sourceDebounceTimerRef.current) {
                clearTimeout(sourceDebounceTimerRef.current);
            }
        };
    }, []);


    const [calibration, setCalibration] = useState<{ active: boolean, progress: number }>({ active: true, progress: 0 });
    const [actionSummary, setActionSummary] = useState<ActionSummary>(DEFAULT_ACTION_SUMMARY);

    const applyProvisionalManualVitals = useCallback((submittedVitals: ManualSubmittedVitals) => {
        setLiveVitals(prev => ({
            ...prev,
            heartRate: Math.round(submittedVitals.bpm),
            hrv: Math.round(submittedVitals.hrv),
            spO2: Math.round(submittedVitals.spo2),
            skinTemp: submittedVitals.temperature,
            trend: 'Manual update pending score',
        }));
    }, []);

    useEffect(() => {
        if (selectedMode !== 'manual') {
            return;
        }

        setLiveVitals(defaultVitals);
        setCalibration({ active: true, progress: 0 });
        setActionSummary({
            ...DEFAULT_ACTION_SUMMARY,
            status: 'Manual mode',
            why: 'Enter a manual reading to update the monitor.',
            next_step: 'Submit a manual reading below.',
            advice_strength: 'calibration',
        });
    }, [selectedMode]);

    // Handle reading response from sensor simulator
    const handleReadingResponse = useCallback((_reading: any, response: any) => {
        console.log('[Dashboard] handleReadingResponse called:', response);
        requestSourceSwitch(response?.source || 'simulator');

        if (response.status === 'retake_requested') {
            setActionSummary(getActionSummaryFromResponse(response));
            return;
        }

        if (response.status === 'calibrating') {
            setCalibration({
                active: true,
                progress: (response.readings_collected || 0) / (response.readings_needed || 15)
            });
            setActionSummary(getActionSummaryFromResponse(response));
        } else if (response.status === 'scored' && response.components) {
            console.log('[Dashboard] Updating vitals with:', response.components);
            setCalibration({ active: false, progress: 1 });
            setLiveVitals({
                heartRate: Math.round(response.components.heart_rate.value),
                hrv: Math.round(response.components.hrv.value),
                spO2: Math.round(response.components.spo2.value),
                skinTemp: response.components.temperature.value,
                score: Math.round(response.score),
                trend: response.zone_label || 'Optimal'
            });
            setActionSummary(getActionSummaryFromResponse(response));
        }
    }, [requestSourceSwitch]);

    // Sensor simulator - sends mock biometric data to backend
    // This simulates what the hardware would do in production
    const simulatorEnabled = modeFlags.enableSimulator && activeView === 'overview' && !!sessionId;

    useSensorSimulator({
        sessionId,
        enabled: simulatorEnabled,
        intervalMs: 1000, // Send reading every 1 second for even faster calibration
        onReading: handleReadingResponse,
    });

    // Fallback: Poll Score API only if sensor simulator isn't providing data
    // This is mainly for when connecting to real hardware that doesn't use the simulator
    useEffect(() => {
        const shouldPollScore = modeFlags.enableScorePolling
            && activeView === 'overview'
            && !!sessionId
            && !simulatorEnabled;

        if (!shouldPollScore) return;

        const pollScore = async () => {
            try {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                const data: ScoreResponse = await api.getScore(sessionId);

                if (data.status === 'calibrating') {
                    requestSourceSwitch(data.source || 'hardware');
                    setCalibration({
                        active: true,
                        progress: (data.readings_collected || 0) / (data.readings_needed || 15)
                    });
                    setActionSummary(getActionSummaryFromResponse(data));
                } else if (data.status === 'retake_requested') {
                    setActionSummary(getActionSummaryFromResponse(data));
                } else if (data.status === 'scored') {
                    requestSourceSwitch(data.source || 'hardware');
                    setCalibration({ active: false, progress: 1 });
                    setLiveVitals(prev => ({
                        ...prev,
                        heartRate: data.components ? Math.round(data.components.heart_rate.value) : prev.heartRate,
                        hrv: data.components ? Math.round(data.components.hrv.value) : prev.hrv,
                        spO2: data.components ? Math.round(data.components.spo2.value) : prev.spO2,
                        skinTemp: data.components ? data.components.temperature.value : prev.skinTemp,
                        score: data.score !== undefined ? Math.round(data.score) : prev.score,
                        trend: data.zone_label || prev.trend || 'Optimal'
                    }));
                    setActionSummary(getActionSummaryFromResponse(data));
                }
            } catch (err) {
                const message = err instanceof Error ? err.message : String(err);
                console.error(`[CardioTwin] Score API failed: ${message}. Falling back to mock data.`);
                // Graceful fallback mock data
                setCalibration({ active: false, progress: 1 });
                setLiveVitals({
                    heartRate: 62 + Math.floor(Math.random() * 5),
                    hrv: 58 + Math.floor(Math.random() * 4),
                    spO2: 98 + Math.floor(Math.random() * 2),
                    skinTemp: 36.4 + Math.random() * 0.4,
                    score: 94,
                    trend: 'Thriving'
                });
                setActionSummary(DEFAULT_ACTION_SUMMARY);
            }
        };

        const interval = setInterval(pollScore, 2000);
        pollScore(); // Initial fetch
        return () => clearInterval(interval);
    }, [activeView, modeFlags.enableScorePolling, requestSourceSwitch, sessionId, simulatorEnabled]);

    // On-demand nudge fetch
    const fetchNudge = useCallback(async () => {
        if (!sessionId) return;
        setIsLoadingNudge(true);
        try {
            const data = await api.getNudge(sessionId);
            console.log(`[CardioTwin] AI Nudge received:`, data.message);
            setNudge(data);
            setShowNudge(true);
        } catch (err) {
            const message = err instanceof Error ? err.message : String(err);
            console.error(`[CardioTwin] Nudge API failed: ${message}. Using fallback nudge.`);
            setNudge({
                message: 'Remember to stay hydrated and take regular breaks for your heart health! 💚',
                zone: 'GREEN',
                zone_label: 'General Tip',
                phone: null,
            });
            setShowNudge(true);
        } finally {
            setIsLoadingNudge(false);
        }
    }, [sessionId]);


    return (
        <div className="bg-background-light text-background-dark h-screen overflow-hidden font-display flex flex-col pb-16 md:pb-0">
            {/* Top Navigation Bar */}
            <header className="sticky top-0 z-50 w-full border-b border-primary/10 bg-white/95 backdrop-blur-md shadow-[0_4px_20px_rgb(0,0,0,0.02)]">
                <div className="w-full px-3 sm:px-6 h-14 md:h-16 flex items-center justify-between">
                    <Link to="/" className="flex items-center gap-2 sm:gap-3">
                        <div className="text-primary bg-primary/10 p-1.5 sm:p-2 rounded-xl">
                            <Activity className="w-5 h-5 sm:w-6 sm:h-6" />
                        </div>
                        <div>
                            <h1 className="text-lg sm:text-xl font-bold tracking-tight">CardioTwin <span className="text-primary italic font-serif">AI</span></h1>
                        </div>
                    </Link>

                    <div className="flex items-center gap-2 sm:gap-6">
                        <div className="flex items-center gap-1.5 sm:gap-2 bg-primary/10 px-2 sm:px-3 py-1 sm:py-1.5 rounded-full border border-primary/20 shadow-sm">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                            </span>
                            <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider text-primary">{t('dash.liveStatus')}</span>
                        </div>
                        <div className="flex items-center gap-1.5 sm:gap-2 bg-slate-100 px-2 sm:px-3 py-1 sm:py-1.5 rounded-full border border-slate-200 shadow-sm">
                            <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider text-slate-600">Source</span>
                            <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider text-slate-800">{activeSource}</span>
                        </div>
                        <button
                            onClick={toggleMode}
                            className="flex items-center gap-1.5 sm:gap-2 bg-indigo-100 px-2 sm:px-3 py-1 sm:py-1.5 rounded-full border border-indigo-200 shadow-sm hover:bg-indigo-200 transition-colors"
                            title="Toggle mode"
                        >
                            <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider text-indigo-600">Mode</span>
                            <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider text-indigo-800">{selectedMode}</span>
                        </button>
                        <div className="hidden sm:block h-8 w-[1px] bg-background-dark/10"></div>
                        <div className="flex items-center gap-2 sm:gap-3">
                            <button
                                onClick={() => setActiveView('settings')}
                                className="p-1.5 sm:p-2 bg-background-light hover:bg-primary/10 rounded-xl transition-colors text-background-dark/60 hover:text-primary relative shadow-sm border border-transparent hover:border-primary/20"
                            >
                                <Bell className="w-4 h-4 sm:w-5 sm:h-5" />
                                <span className="absolute top-1 right-1 sm:top-1.5 sm:right-1.5 w-2 h-2 sm:w-2.5 sm:h-2.5 bg-rose-500 rounded-full border-2 border-white"></span>
                            </button>
                            <div className="h-8 w-8 sm:h-10 sm:w-10 rounded-full overflow-hidden border-2 border-primary/20 shadow-sm">
                                <img
                                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuBWXOkTJMP_6l_TFoYjjjmGFjdU6zuDygl_fyTXXnHnGQmH6D8Uea5Vsepca75gCDkc4FztOnI9hV-AAFUzuWPquePJvfdmd9Z7VVjfd-a6IMk9m0SLbuTvSu_s-en5fL3C0vrE89DgKJaOrAZMcefaritp3iJbH1TFSZZTJCMYQFCQSbvXn8mXYKTLbpbniUh_Tld86lZN6eMTc_9F7X-DcwFKoeqNB8khRla_bbGvXdmGtr55EjrWULm-3ln3lE35aD04nOukHAw"
                                    alt="Medical professional"
                                    className="w-full h-full object-cover"
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            <div className="flex flex-1 overflow-hidden">
                <Sidebar activeView={activeView} setActiveView={setActiveView} />

                <main className="flex-1 overflow-y-auto p-3 sm:p-6 md:p-8">
                    {activeView === 'overview' && (
                        <div className="space-y-4 sm:space-y-6 max-w-6xl mx-auto flex flex-col min-h-[calc(100vh-8rem)] pb-8">
                            <div className="flex flex-col sm:flex-row sm:items-end justify-between shrink-0 mb-2 gap-3">
                                <div>
                                    <h2 className="text-xl sm:text-2xl md:text-3xl font-extrabold flex flex-wrap items-center gap-2 sm:gap-3 tracking-tight">
                                        CardioTwin <span className="italic font-serif text-primary font-normal">{t('dash.digitalTwin')}</span>
                                        {calibration.active ? (
                                            <span className="text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider bg-orange-100 text-orange-600 border border-orange-200 shadow-sm animate-pulse">
                                                {t('dash.calibrating')}
                                            </span>
                                        ) : (
                                            <span className="text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider bg-emerald-100 text-emerald-600 border border-emerald-200 shadow-sm">
                                                {t('dash.liveMonitoring')}
                                            </span>
                                        )}
                                    </h2>
                                    <p className="text-background-dark/60 mt-1 font-medium text-xs sm:text-sm truncate max-w-[280px] sm:max-w-none">{t('dash.session')}: {sessionId} • {t('dash.realtimeSync')}</p>
                                </div>
                                {!calibration.active && (
                                    <div className="flex items-center gap-3 sm:gap-4">
                                        <button
                                            onClick={fetchNudge}
                                            disabled={isLoadingNudge}
                                            className="flex items-center gap-2 px-3 sm:px-4 py-2 sm:py-2.5 rounded-xl bg-primary/10 hover:bg-primary/20 text-primary text-xs sm:text-sm font-bold transition-all border border-primary/20 hover:border-primary/30 cursor-pointer disabled:opacity-50 shadow-sm hover:shadow-md"
                                        >
                                            <Sparkles className={`w-4 h-4 ${isLoadingNudge ? 'animate-spin' : ''}`} />
                                            <span className="hidden sm:inline">{isLoadingNudge ? t('dash.loading') : t('dash.getAiAdvice')}</span>
                                            <span className="sm:hidden">{isLoadingNudge ? '...' : 'AI'}</span>
                                        </button>
                                        <div className="text-right flex flex-col items-end bg-white rounded-xl border border-background-dark/10 px-3 py-2 shadow-sm min-w-[120px]">
                                            <span className="text-[10px] sm:text-xs uppercase font-bold text-background-dark/50 tracking-wider">{t('dash.healthScore')}</span>
                                            <span className={`text-xl sm:text-2xl font-black ${liveVitals.score >= 80 ? 'text-primary' : liveVitals.score >= 55 ? 'text-yellow-500' : liveVitals.score >= 30 ? 'text-orange-500' : 'text-rose-500'}`}>
                                                {liveVitals.score}
                                            </span>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {!calibration.active && (
                                <section className="bg-white rounded-2xl border border-primary/10 shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-4 sm:p-5 grid grid-cols-1 lg:grid-cols-12 gap-3">
                                    <div className="lg:col-span-3">
                                        <p className="text-[10px] uppercase tracking-widest font-bold text-background-dark/40">Status</p>
                                        <p className="text-base sm:text-lg font-extrabold text-background-dark mt-1">{actionSummary.status}</p>
                                        <div className="mt-2 flex flex-wrap gap-2">
                                            <span className="text-[10px] uppercase font-bold px-2 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                                                Confidence: {actionSummary.confidence_level}
                                            </span>
                                            <span className="text-[10px] uppercase font-bold px-2 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                                                Signal: {actionSummary.signal_quality}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="lg:col-span-4">
                                        <p className="text-[10px] uppercase tracking-widest font-bold text-background-dark/40">Why</p>
                                        <p className="text-sm text-background-dark/80 mt-1 font-medium">{actionSummary.why}</p>
                                        <p className="text-[10px] text-background-dark/50 mt-2">Confidence score: {(actionSummary.signal_confidence * 100).toFixed(0)}%</p>
                                    </div>
                                    <div className="lg:col-span-3">
                                        <p className="text-[10px] uppercase tracking-widest font-bold text-background-dark/40">Next step</p>
                                        <p className="text-sm text-background-dark/80 mt-1 font-medium">{actionSummary.next_step}</p>
                                        <p className="text-[10px] text-rose-600 mt-2 font-semibold">{actionSummary.if_symptoms}</p>
                                    </div>
                                    <div className="lg:col-span-2">
                                        <p className="text-[10px] uppercase tracking-widest font-bold text-background-dark/40">Top drivers</p>
                                        <div className="mt-1 space-y-2">
                                            {(actionSummary.drivers || []).slice(0, 2).map((driver) => (
                                                <div key={driver.code} className="rounded-xl border border-background-dark/10 bg-background-light/50 px-2.5 py-2">
                                                    <p className="text-xs font-bold text-background-dark">{driver.label}</p>
                                                    <p className="text-[10px] text-background-dark/60 mt-0.5">{driver.detail}</p>
                                                </div>
                                            ))}
                                            {(!actionSummary.drivers || actionSummary.drivers.length === 0) && (
                                                <p className="text-xs text-background-dark/60">No dominant drivers yet.</p>
                                            )}
                                        </div>
                                    </div>
                                </section>
                            )}

                            <div className="flex-1 relative bg-white rounded-2xl sm:rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-primary/10 overflow-hidden flex items-center justify-center min-h-[350px] sm:min-h-[450px] md:min-h-[600px] w-full mt-2 sm:mt-4">
                                {/* Clinical background */}
                                <div className="absolute inset-0 bg-[linear-gradient(160deg,#f8fbfd_0%,#eff6f8_48%,#f9fcff_100%)] pointer-events-none"></div>
                                <div className="absolute inset-0 opacity-40 pointer-events-none bg-[linear-gradient(to_right,rgba(56,189,248,0.12)_1px,transparent_1px),linear-gradient(to_bottom,rgba(56,189,248,0.12)_1px,transparent_1px)] bg-[size:28px_28px]"></div>
                                <div className="absolute -top-16 -left-16 w-[260px] sm:w-[360px] h-[260px] sm:h-[360px] bg-cyan-200/35 blur-[90px] rounded-full pointer-events-none"></div>
                                <div className="absolute -bottom-20 -right-10 w-[260px] sm:w-[340px] h-[260px] sm:h-[340px] bg-emerald-200/25 blur-[95px] rounded-full pointer-events-none"></div>

                                {calibration.active ? (
                                    <div className="relative z-10 flex flex-col items-center max-w-md w-full p-5 sm:p-8 mx-3 text-center bg-white/80 backdrop-blur-md rounded-2xl sm:rounded-3xl border border-primary/20 shadow-xl">
                                        <Activity className="w-10 h-10 sm:w-12 sm:h-12 text-primary animate-bounce mb-4 sm:mb-6" />
                                        <h3 className="text-xl sm:text-2xl font-bold text-background-dark mb-2">{t('dash.analyzingBaseline')}</h3>
                                        <p className="text-background-dark/60 mb-6 sm:mb-8 font-medium text-sm sm:text-base">{t('dash.gatheringSensor')}</p>

                                        <div className="w-full h-3 bg-background-light rounded-full overflow-hidden border border-background-dark/10">
                                            <div
                                                className="h-full bg-primary transition-all duration-500 rounded-full bg-[length:2rem_2rem] bg-[linear-gradient(45deg,rgba(255,255,255,.15)_25%,transparent_25%,transparent_50%,rgba(255,255,255,.15)_50%,rgba(255,255,255,.15)_75%,transparent_75%,transparent)] animate-[progress-stripes_1s_linear_infinite]"
                                                style={{ width: `${Math.min(100, Math.max(5, calibration.progress * 100))}%` }}
                                            ></div>
                                        </div>
                                        <div className="flex justify-between w-full mt-3 text-xs font-bold text-background-dark/50 uppercase tracking-widest">
                                            <span>{t('dash.initializing')}</span>
                                            <span>{Math.min(100, Math.round(calibration.progress * 100))}%</span>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="flex flex-col md:flex-row gap-4 w-full h-full min-h-[350px] sm:min-h-[450px] md:min-h-[600px]">
                                        {/* 3D Body Render — shifts left when panel is open */}
                                        <div className={`relative h-full min-h-[350px] sm:min-h-[450px] md:min-h-[700px] flex items-center justify-center z-10 transition-all duration-500 ease-in-out ${showNudge ? 'md:flex-[3]' : 'flex-1'}`}>
                                            <div className="absolute inset-x-0 top-0 bottom-[92px] sm:bottom-[124px] rounded-2xl sm:rounded-3xl overflow-hidden pointer-events-auto">
                                                <Canvas
                                                    shadows
                                                    camera={{ position: [0, 1.45, 7.6], fov: 37 }}
                                                    dpr={[1, 2]}
                                                    performance={{ min: 0.5 }}
                                                >
                                                    <Suspense fallback={
                                                        <mesh>
                                                            <boxGeometry args={[1, 2, 0.5]} />
                                                            <meshStandardMaterial color="#e5e7eb" wireframe />
                                                        </mesh>
                                                    }>
                                                        <ambientLight intensity={0.6} />
                                                        <spotLight position={[5, 5, 5]} intensity={1.5} angle={0.5} penumbra={1} castShadow />
                                                        <Environment preset="city" />

                                                        <HealthAvatar score={liveVitals.score} vitals={liveVitals} />

                                                        <OrbitControls
                                                            enablePan={false}
                                                            makeDefault
                                                            target={[0, 1.25, 0]}
                                                            minPolarAngle={Math.PI / 6}
                                                            maxPolarAngle={Math.PI / 1.5}
                                                            minDistance={5.9}
                                                            maxDistance={10}
                                                            zoomSpeed={1.5}
                                                        />
                                                    </Suspense>
                                                </Canvas>
                                            </div>

                                            {/* Bottom Floating Info Panel */}
                                            <div className="absolute bottom-4 sm:bottom-8 left-1/2 -translate-x-1/2 w-[94%] sm:w-[90%] max-w-2xl bg-white/90 backdrop-blur-xl p-3 sm:p-5 rounded-2xl sm:rounded-3xl shadow-[0_8px_40px_rgba(0,0,0,0.08)] border border-primary/20 flex items-center justify-between z-20">
                                                <div className="flex items-center gap-2 sm:gap-4">
                                                    <div className="p-2 sm:p-3 bg-primary/10 rounded-xl sm:rounded-2xl border border-primary/20">
                                                        <BrainCircuit className="w-4 h-4 sm:w-6 sm:h-6 text-primary" />
                                                    </div>
                                                    <div>
                                                        <h4 className="text-xs sm:text-sm font-bold text-background-dark mb-0.5">{t('dash.analysisStatus')}</h4>
                                                        <p className="text-[10px] sm:text-xs text-background-dark/60 font-medium max-w-[150px] sm:max-w-md">
                                                            {liveVitals.score >= 80
                                                                ? t('dash.statusOptimal')
                                                                : liveVitals.score >= 55
                                                                    ? t('dash.statusMild')
                                                                    : t('dash.statusWarning')}
                                                        </p>
                                                    </div>
                                                </div>
                                                <div className="text-right pl-2 sm:pl-4 border-l border-background-dark/10">
                                                    <span className="text-[10px] font-bold text-background-dark/40 uppercase tracking-widest block mb-1 sm:mb-1.5 w-max">{t('dash.activeZone')}</span>
                                                    <span className={`px-2 sm:px-4 py-1 sm:py-1.5 rounded-full text-[10px] sm:text-xs font-bold border whitespace-nowrap ${liveVitals.score >= 80 ? 'bg-emerald-100 text-emerald-700 border-emerald-200' : liveVitals.score >= 55 ? 'bg-yellow-100 text-yellow-700 border-yellow-200' : liveVitals.score >= 30 ? 'bg-orange-100 text-orange-700 border-orange-200' : 'bg-rose-100 text-rose-700 border-rose-200'}`}>
                                                        {liveVitals.trend || "Thriving"}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* AI Advice Panel — overlay on mobile, side panel on desktop */}
                                        {showNudge && nudge && (
                                            <>
                                                {/* Mobile: full-screen overlay */}
                                                <div className="md:hidden fixed inset-0 z-50 bg-black/30 backdrop-blur-sm flex items-end sm:items-center justify-center p-3 pb-20" onClick={() => setShowNudge(false)}>
                                                    <div className="w-full max-w-md max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
                                                        <NudgePanel
                                                            nudge={nudge}
                                                            isLoading={isLoadingNudge}
                                                            onRefresh={fetchNudge}
                                                            onClose={() => setShowNudge(false)}
                                                        />
                                                    </div>
                                                </div>
                                                {/* Desktop: side panel */}
                                                <div className="hidden md:block flex-[2] min-w-[280px] max-w-[380px] transition-all duration-500 ease-in-out">
                                                    <NudgePanel
                                                        nudge={nudge}
                                                        isLoading={isLoadingNudge}
                                                        onRefresh={fetchNudge}
                                                        onClose={() => setShowNudge(false)}
                                                    />
                                                </div>
                                            </>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {activeView === 'projection' && sessionId && (
                        <div className="max-w-4xl mx-auto py-4 sm:py-8">
                            <ProjectionPanel
                                sessionId={sessionId}
                                currentScore={liveVitals.score}
                                currentVitals={{
                                    heartRate: liveVitals.heartRate,
                                    hrv: liveVitals.hrv,
                                    spO2: liveVitals.spO2,
                                    skinTemp: liveVitals.skinTemp,
                                }}
                            />
                        </div>
                    )}

                    {activeView === 'history' && sessionId && (
                        <div className="max-w-4xl mx-auto py-4 sm:py-8 h-[calc(100vh-10rem)] md:h-[calc(100vh-12rem)]">
                            <HistoryChart sessionId={sessionId} />
                        </div>
                    )}

                    {activeView === 'manual' && sessionId && (
                        <div className="max-w-lg mx-auto py-4 sm:py-8">
                            <ManualInputPanel sessionId={sessionId} onReadingSubmitted={(result, submittedVitals) => {
                                requestSourceSwitch(result?.source || 'manual');
                                applyProvisionalManualVitals(submittedVitals);

                                if (result.status === 'calibrating') {
                                    setCalibration({
                                        active: true,
                                        progress: (result.readings_collected || 0) / (result.readings_needed || 5)
                                    });
                                    setActionSummary(getActionSummaryFromResponse(result));
                                    return;
                                }

                                if (result.status === 'retake_requested') {
                                    setActionSummary(getActionSummaryFromResponse(result));
                                    return;
                                }

                                if (result.status === 'scored' && result.components) {
                                    setCalibration({ active: false, progress: 1 });
                                    setLiveVitals({
                                        heartRate: Math.round(result.components.heart_rate.value),
                                        hrv: Math.round(result.components.hrv.value),
                                        spO2: Math.round(result.components.spo2.value),
                                        skinTemp: result.components.temperature.value,
                                        score: Math.round(result.score),
                                        trend: result.zone_label || 'Optimal',
                                    });
                                    setActionSummary(getActionSummaryFromResponse(result));
                                    setActiveView('overview');
                                }
                            }} />
                        </div>
                    )}

                    {activeView === 'settings' && (
                        <div className="max-w-2xl mx-auto py-4 sm:py-8">
                            <h2 className="text-2xl sm:text-3xl font-extrabold text-background-dark mb-6 sm:mb-8 tracking-tight">{t('settings.title')}</h2>

                            {/* Language Settings Card */}
                            <div className="bg-white rounded-2xl sm:rounded-3xl border border-primary/10 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden">
                                <div className="px-4 sm:px-8 py-4 sm:py-6 border-b border-background-light">
                                    <div className="flex items-center gap-3 mb-1">
                                        <Globe className="w-5 h-5 text-primary" />
                                        <h3 className="text-base sm:text-lg font-bold text-background-dark">{t('settings.language')}</h3>
                                    </div>
                                    <p className="text-xs sm:text-sm text-background-dark/60 font-medium ml-8">{t('settings.languageDesc')}</p>
                                </div>

                                <div className="p-4 sm:p-6 grid grid-cols-1 sm:grid-cols-2 gap-3">
                                    {LANGUAGE_OPTIONS.map((option) => {
                                        const isActive = lang === option.code;
                                        return (
                                            <button
                                                key={option.code}
                                                onClick={() => setLang(option.code)}
                                                className={`relative flex items-center gap-4 p-4 rounded-2xl border-2 transition-all duration-200 cursor-pointer group ${isActive
                                                        ? 'border-primary bg-primary/5 shadow-md shadow-primary/10'
                                                        : 'border-background-dark/10 bg-white hover:border-primary/30 hover:bg-primary/[0.02] hover:shadow-sm'
                                                    }`}
                                            >
                                                <span className="text-2xl">{option.flag}</span>
                                                <div className="text-left">
                                                    <div className={`font-bold text-sm ${isActive ? 'text-primary' : 'text-background-dark'}`}>
                                                        {option.label}
                                                    </div>
                                                    <div className="text-xs text-background-dark/50 font-medium">
                                                        {t(`lang.${option.code}`)}
                                                    </div>
                                                </div>
                                                {isActive && (
                                                    <div className="absolute top-3 right-3 w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                                                        <Check className="w-3.5 h-3.5 text-white" />
                                                    </div>
                                                )}
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
}
