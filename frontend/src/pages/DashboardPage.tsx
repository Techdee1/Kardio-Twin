import { useState, useEffect, useCallback, Suspense } from 'react';
import { Activity, Bell, BrainCircuit, Sparkles, Globe, Check } from 'lucide-react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import Sidebar from '../components/dashboard/Sidebar';
import NudgePanel from '../components/dashboard/NudgePanel';
import { api } from '../services/api';
import type { NudgeResponse } from '../services/api';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment } from '@react-three/drei';
import { HealthAvatar } from '../components/HealthAvatar';
import { useLanguage, LANGUAGE_OPTIONS } from '../i18n/LanguageContext';
import { useSensorSimulator } from '../hooks/useSensorSimulator';

export interface Vitals {
    heartRate: number;
    hrv: number;
    spO2: number;
    skinTemp: number;
    score: number;
    trend: string;
}

export default function DashboardPage() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const sessionId = searchParams.get('session_id');
    const { lang, setLang, t } = useLanguage();

    const [activeView, setActiveView] = useState<'overview' | 'settings'>('overview');

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

    // Initial load check
    useEffect(() => {
        if (!sessionId) {
            navigate('/');
        }
    }, [sessionId, navigate]);


    const [calibration, setCalibration] = useState<{ active: boolean, progress: number }>({ active: true, progress: 0 });

    // Handle reading response from sensor simulator
    const handleReadingResponse = useCallback((reading: any, response: any) => {
        console.log('[Dashboard] handleReadingResponse called:', response);
        if (response.status === 'calibrating') {
            setCalibration({
                active: true,
                progress: (response.readings_collected || 0) / (response.readings_needed || 15)
            });
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
        }
    }, []);

    // Sensor simulator - sends mock biometric data to backend
    // This simulates what the hardware would do in production
    useSensorSimulator({
        sessionId,
        enabled: activeView === 'overview' && !!sessionId,
        intervalMs: 2000, // Send reading every 2 seconds
        onReading: handleReadingResponse,
    });

    // Fallback: Poll Score API only if sensor simulator isn't providing data
    // This is mainly for when connecting to real hardware that doesn't use the simulator
    useEffect(() => {
        if (activeView !== 'overview' || !sessionId) return;
        
        // Skip polling if we're using the sensor simulator (which provides data via onReading)
        // Only poll as a fallback for real hardware connections
        const skipPolling = true; // Sensor simulator is active
        if (skipPolling) return;

        const pollScore = async () => {
            try {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                const data: any = await api.getScore(sessionId);

                if (data.status === 'calibrating') {
                    setCalibration({
                        active: true,
                        progress: (data.readings_collected || 0) / (data.readings_needed || 15)
                    });
                } else if (data.components) {
                    setCalibration({ active: false, progress: 1 });
                    setLiveVitals(prev => ({
                        ...prev,
                        heartRate: Math.round(data.components.heart_rate.value),
                        hrv: Math.round(data.components.hrv.value),
                        spO2: Math.round(data.components.spo2.value),
                        skinTemp: data.components.temperature.value,
                        score: Math.round(data.score),
                        trend: data.zone_label || 'Optimal'
                    }));
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
            }
        };

        const interval = setInterval(pollScore, 2000);
        pollScore(); // Initial fetch
        return () => clearInterval(interval);
    }, [activeView, sessionId]);

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
        <div className="bg-background-light text-background-dark h-screen overflow-hidden font-display flex flex-col">
            {/* Top Navigation Bar */}
            <header className="sticky top-0 z-50 w-full border-b border-primary/10 bg-white/95 backdrop-blur-md shadow-[0_4px_20px_rgb(0,0,0,0.02)]">
                <div className="w-full px-6 h-16 flex items-center justify-between">
                    <Link to="/" className="flex items-center gap-3">
                        <div className="text-primary bg-primary/10 p-2 rounded-xl">
                            <Activity className="w-6 h-6" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold tracking-tight">CardioTwin <span className="text-primary italic font-serif">AI</span></h1>
                        </div>
                    </Link>

                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-2 bg-primary/10 px-3 py-1.5 rounded-full border border-primary/20 shadow-sm">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                            </span>
                            <span className="text-xs font-bold uppercase tracking-wider text-primary">{t('dash.liveStatus')}</span>
                        </div>
                        <div className="h-8 w-[1px] bg-background-dark/10"></div>
                        <div className="flex items-center gap-3">
                            <button
                                onClick={() => setActiveView('settings')}
                                className="p-2 bg-background-light hover:bg-primary/10 rounded-xl transition-colors text-background-dark/60 hover:text-primary relative shadow-sm border border-transparent hover:border-primary/20"
                            >
                                <Bell className="w-5 h-5" />
                                <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-rose-500 rounded-full border-2 border-white"></span>
                            </button>
                            <div className="h-10 w-10 rounded-full overflow-hidden border-2 border-primary/20 shadow-sm">
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

                <main className="flex-1 overflow-y-auto p-6 md:p-8">
                    {activeView === 'overview' && (
                        <div className="space-y-6 max-w-6xl mx-auto flex flex-col min-h-[calc(100vh-8rem)] pb-8">
                            <div className="flex items-end justify-between shrink-0 mb-2">
                                <div>
                                    <h2 className="text-3xl font-extrabold flex items-center gap-3 tracking-tight">
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
                                    <p className="text-background-dark/60 mt-1 font-medium">{t('dash.session')}: {sessionId} • {t('dash.realtimeSync')}</p>
                                </div>
                                {!calibration.active && (
                                    <div className="flex items-center gap-4">
                                        <button
                                            onClick={fetchNudge}
                                            disabled={isLoadingNudge}
                                            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary/10 hover:bg-primary/20 text-primary text-sm font-bold transition-all border border-primary/20 hover:border-primary/30 cursor-pointer disabled:opacity-50 shadow-sm hover:shadow-md"
                                        >
                                            <Sparkles className={`w-4 h-4 ${isLoadingNudge ? 'animate-spin' : ''}`} />
                                            {isLoadingNudge ? t('dash.loading') : t('dash.getAiAdvice')}
                                        </button>
                                        <div className="text-right flex flex-col items-end">
                                            <span className="text-xs uppercase font-bold text-background-dark/50 tracking-wider">{t('dash.healthScore')}</span>
                                            <span className={`text-5xl font-black ${liveVitals.score >= 80 ? 'text-primary' : liveVitals.score >= 55 ? 'text-yellow-500' : liveVitals.score >= 30 ? 'text-orange-500' : 'text-rose-500'}`}>
                                                {liveVitals.score}
                                            </span>
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="flex-1 relative bg-white rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-primary/10 overflow-hidden flex items-center justify-center min-h-[600px] w-full mt-4">
                                {/* Background glow */}
                                <div className="absolute inset-0 bg-primary/5 opacity-40 pointer-events-none"></div>
                                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/10 blur-[120px] rounded-full"></div>

                                {calibration.active ? (
                                    <div className="relative z-10 flex flex-col items-center max-w-md w-full p-8 text-center bg-white/80 backdrop-blur-md rounded-3xl border border-primary/20 shadow-xl">
                                        <Activity className="w-12 h-12 text-primary animate-bounce mb-6" />
                                        <h3 className="text-2xl font-bold text-background-dark mb-2">{t('dash.analyzingBaseline')}</h3>
                                        <p className="text-background-dark/60 mb-8 font-medium">{t('dash.gatheringSensor')}</p>

                                        <div className="w-full h-3 bg-background-light rounded-full overflow-hidden border border-background-dark/10">
                                            <div
                                                className="h-full bg-primary transition-all duration-500 rounded-full bg-[length:2rem_2rem] bg-[linear-gradient(45deg,rgba(255,255,255,.15)_25%,transparent_25%,transparent_50%,rgba(255,255,255,.15)_50%,rgba(255,255,255,.15)_75%,transparent_75%,transparent)] animate-[progress-stripes_1s_linear_infinite]"
                                                style={{ width: `${Math.max(5, calibration.progress * 100)}%` }}
                                            ></div>
                                        </div>
                                        <div className="flex justify-between w-full mt-3 text-xs font-bold text-background-dark/50 uppercase tracking-widest">
                                            <span>{t('dash.initializing')}</span>
                                            <span>{Math.round(calibration.progress * 100)}%</span>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="flex gap-4 w-full h-full min-h-[600px]">
                                        {/* 3D Body Render — shifts left when panel is open */}
                                        <div className={`relative h-full min-h-[700px] flex items-center justify-center z-10 transition-all duration-500 ease-in-out ${showNudge ? 'flex-[3]' : 'flex-1'}`}>
                                            <div className="absolute inset-0 translate-y-4 rounded-3xl overflow-hidden pointer-events-auto">
                                                <Canvas shadows camera={{ position: [0, 1, 6], fov: 35 }}>
                                                    <Suspense fallback={null}>
                                                        <ambientLight intensity={0.6} />
                                                        <spotLight position={[5, 5, 5]} intensity={1.5} angle={0.5} penumbra={1} castShadow />
                                                        <Environment preset="city" />

                                                        <HealthAvatar score={liveVitals.score} vitals={liveVitals} />

                                                        <OrbitControls
                                                            enablePan={false}
                                                            makeDefault
                                                            minPolarAngle={Math.PI / 6}
                                                            maxPolarAngle={Math.PI / 1.5}
                                                            minDistance={1.5}
                                                            maxDistance={15}
                                                            zoomSpeed={1.5}
                                                        />
                                                    </Suspense>
                                                </Canvas>
                                            </div>

                                            {/* Bottom Floating Info Panel */}
                                            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 w-[90%] max-w-2xl bg-white/90 backdrop-blur-xl p-5 rounded-3xl shadow-[0_8px_40px_rgba(0,0,0,0.08)] border border-primary/20 flex items-center justify-between z-20">
                                                <div className="flex items-center gap-4">
                                                    <div className="p-3 bg-primary/10 rounded-2xl border border-primary/20">
                                                        <BrainCircuit className="w-6 h-6 text-primary" />
                                                    </div>
                                                    <div>
                                                        <h4 className="text-sm font-bold text-background-dark mb-0.5">{t('dash.analysisStatus')}</h4>
                                                        <p className="text-xs text-background-dark/60 font-medium max-w-md">
                                                            {liveVitals.score >= 80
                                                                ? t('dash.statusOptimal')
                                                                : liveVitals.score >= 55
                                                                    ? t('dash.statusMild')
                                                                    : t('dash.statusWarning')}
                                                        </p>
                                                    </div>
                                                </div>
                                                <div className="text-right pl-4 border-l border-background-dark/10">
                                                    <span className="text-[10px] font-bold text-background-dark/40 uppercase tracking-widest block mb-1.5 w-max">{t('dash.activeZone')}</span>
                                                    <span className={`px-4 py-1.5 rounded-full text-xs font-bold border whitespace-nowrap ${liveVitals.score >= 80 ? 'bg-emerald-100 text-emerald-700 border-emerald-200' : liveVitals.score >= 55 ? 'bg-yellow-100 text-yellow-700 border-yellow-200' : liveVitals.score >= 30 ? 'bg-orange-100 text-orange-700 border-orange-200' : 'bg-rose-100 text-rose-700 border-rose-200'}`}>
                                                        {liveVitals.trend || "Thriving"}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* AI Advice Panel */}
                                        {showNudge && nudge && (
                                            <div className="flex-[2] min-w-[280px] max-w-[380px] transition-all duration-500 ease-in-out">
                                                <NudgePanel
                                                    nudge={nudge}
                                                    isLoading={isLoadingNudge}
                                                    onRefresh={fetchNudge}
                                                    onClose={() => setShowNudge(false)}
                                                />
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {activeView === 'settings' && (
                        <div className="max-w-2xl mx-auto py-8">
                            <h2 className="text-3xl font-extrabold text-background-dark mb-8 tracking-tight">{t('settings.title')}</h2>

                            {/* Language Settings Card */}
                            <div className="bg-white rounded-3xl border border-primary/10 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden">
                                <div className="px-8 py-6 border-b border-background-light">
                                    <div className="flex items-center gap-3 mb-1">
                                        <Globe className="w-5 h-5 text-primary" />
                                        <h3 className="text-lg font-bold text-background-dark">{t('settings.language')}</h3>
                                    </div>
                                    <p className="text-sm text-background-dark/60 font-medium ml-8">{t('settings.languageDesc')}</p>
                                </div>

                                <div className="p-6 grid grid-cols-1 sm:grid-cols-2 gap-3">
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
