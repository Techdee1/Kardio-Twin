import { useState, useEffect, Suspense } from 'react';
import { TrendingDown, TrendingUp, AlertTriangle, ArrowRight, RefreshCw, Calendar, Heart, Activity, Droplets, Thermometer, Sparkles } from 'lucide-react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment } from '@react-three/drei';
import { HealthAvatar } from '../HealthAvatar';
import { api } from '../../services/api';
import type { PredictionResponse } from '../../services/api';
import { useLanguage } from '../../i18n/LanguageContext';

interface ProjectionPanelProps {
    sessionId: string;
    currentScore: number;
    currentVitals: {
        heartRate: number;
        hrv: number;
        spO2: number;
        skinTemp: number;
    };
}

const zoneFromScore = (score: number): string => {
    if (score >= 80) return 'GREEN';
    if (score >= 55) return 'YELLOW';
    if (score >= 30) return 'ORANGE';
    return 'RED';
};

const zoneColors: Record<string, { bg: string; border: string; text: string; badge: string }> = {
    GREEN: { bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-700', badge: 'bg-emerald-100' },
    YELLOW: { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700', badge: 'bg-amber-100' },
    ORANGE: { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-700', badge: 'bg-orange-100' },
    RED: { bg: 'bg-rose-50', border: 'border-rose-200', text: 'text-rose-700', badge: 'bg-rose-100' },
};

/** Render a delta value with arrow + colour. positive = good when isPositiveGood=true */
function DeltaBadge({ delta, unit = '', isPositiveGood = true }: { delta: number; unit?: string; isPositiveGood?: boolean }) {
    if (Math.abs(delta) < 0.05) {
        return <span className="text-xs font-bold text-background-dark/40">—</span>;
    }
    const isGood = isPositiveGood ? delta > 0 : delta < 0;
    const color = isGood ? 'text-emerald-600' : 'text-rose-500';
    const arrow = delta > 0 ? '↑' : '↓';
    return (
        <span className={`text-xs font-black ${color}`}>
            {arrow} {Math.abs(delta).toFixed(1)}{unit}
        </span>
    );
}

/** Minimal markdown → JSX: bold, bullet lists, line breaks */
function SimpleMarkdown({ text }: { text: string }) {
    const lines = String(text || '').split('\n');
    return (
        <div className="space-y-1.5">
            {lines.map((line, i) => {
                if (!line.trim()) return <div key={i} className="h-1" />;
                // Heading lines (## or ###)
                if (line.startsWith('### ')) {
                    return <p key={i} className="text-xs font-black text-background-dark/80 uppercase tracking-wide mt-2">{line.slice(4)}</p>;
                }
                if (line.startsWith('## ')) {
                    return <p key={i} className="text-sm font-black text-background-dark mt-3">{line.slice(3)}</p>;
                }
                // Bullet
                const isBullet = line.startsWith('- ') || line.startsWith('* ');
                const content = isBullet ? line.slice(2) : line;
                // Bold **text**
                const parts = content.split(/\*\*(.*?)\*\*/g);
                const rendered = parts.map((part, j) =>
                    j % 2 === 1 ? <strong key={j} className="font-bold">{part}</strong> : part
                );
                if (isBullet) {
                    return (
                        <div key={i} className="flex gap-2 items-start">
                            <span className="text-primary mt-0.5 shrink-0">•</span>
                            <p className="text-xs text-background-dark/75 leading-relaxed">{rendered}</p>
                        </div>
                    );
                }
                return <p key={i} className="text-xs text-background-dark/75 leading-relaxed">{rendered}</p>;
            })}
        </div>
    );
}

export default function ProjectionPanel({ sessionId, currentScore, currentVitals }: ProjectionPanelProps) {
    const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [days, setDays] = useState(30);
    const [scenario, setScenario] = useState('');
    const [supportsWebGL, setSupportsWebGL] = useState(false);
    const { t } = useLanguage();

    const fetchPrediction = async (nextDays = days, nextScenario = scenario) => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await api.getPrediction({
                session_id: sessionId,
                days: nextDays,
                scenario: nextScenario.trim() || undefined,
            });
            setPrediction(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch prediction');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchPrediction();
    }, [sessionId]);

    useEffect(() => {
        const detectWebGL = () => {
            try {
                const canvas = document.createElement('canvas');
                const context = canvas.getContext('webgl2') || canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                return Boolean(context);
            } catch {
                return false;
            }
        };

        setSupportsWebGL(detectWebGL());
    }, []);

    const currentZone = zoneFromScore(currentScore);
    const projectedZone = prediction ? zoneFromScore(prediction.projected_score) : 'GREEN';
    const scoreChange = prediction ? prediction.projected_score - prediction.current_score : 0;
    const isImproving = scoreChange >= 0;

    const delta = prediction?.projected_vitals_delta;
    const hasScenarioAnalysis = Boolean(scenario.trim()) || Boolean(prediction?.scenario_note) || Boolean(prediction?.ai_review);
    const mapVitalsToAvatar = (vitals?: PredictionResponse['current_vitals']) => ({
        heartRate: vitals?.bpm ?? currentVitals.heartRate,
        hrv: vitals?.hrv ?? currentVitals.hrv,
        spO2: vitals?.spo2 ?? currentVitals.spO2,
        skinTemp: vitals?.temperature ?? currentVitals.skinTemp,
    });
    const projectedAvatarVitals = mapVitalsToAvatar(prediction?.projected_vitals);

    const handleRefresh = () => {
        void fetchPrediction();
    };

    const handleAnalyze = () => {
        void fetchPrediction();
    };

    const renderAvatarPreview = (
        score: number,
        vitals: { heartRate: number; hrv: number; spO2: number; skinTemp: number },
        projected = false,
    ) => {
        if (!supportsWebGL) {
            return (
                <div className="h-full w-full rounded-2xl bg-gradient-to-b from-background-light/70 to-white flex flex-col items-center justify-center px-4 text-center">
                    <div className={`w-16 h-16 rounded-full border-2 ${projected ? 'border-purple-300 bg-purple-100' : 'border-background-dark/10 bg-white'} flex items-center justify-center mb-3`}>
                        <span className={`text-xl font-black ${projected ? 'text-purple-600' : 'text-background-dark/70'}`}>{Math.round(score)}</span>
                    </div>
                    <p className="text-xs font-semibold text-background-dark/70">3D preview unavailable</p>
                    <p className="mt-1 text-[11px] text-background-dark/45">
                        {vitals.heartRate} bpm · {vitals.hrv} ms · {vitals.spO2}% · {vitals.skinTemp.toFixed(1)}°C
                    </p>
                </div>
            );
        }

        return (
            <Canvas camera={{ position: [0, 0, 3], fov: 50 }}>
                <Suspense fallback={null}>
                    <ambientLight intensity={projected ? 0.4 : 0.5} />
                    <directionalLight position={[5, 5, 5]} intensity={projected ? 0.8 : 1} />
                    <Environment preset="city" />
                    <HealthAvatar score={score} vitals={vitals} />
                    <OrbitControls enablePan={false} enableZoom={false} />
                </Suspense>
            </Canvas>
        );
    };

    return (
        <div className="h-full flex flex-col bg-white/80 backdrop-blur-md rounded-3xl border border-primary/10 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden">
            {/* Header */}
            <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-background-dark/5">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 sm:gap-3">
                        <div className="p-1.5 sm:p-2 rounded-xl bg-purple-100 border border-purple-200">
                            <Calendar className="w-4 h-4 sm:w-5 sm:h-5 text-purple-600" />
                        </div>
                        <div>
                            <h3 className="text-base sm:text-lg font-bold text-background-dark">{t('projection.title')}</h3>
                            <p className="text-[10px] sm:text-xs text-background-dark/60">{t('projection.subtitle')}</p>
                        </div>
                    </div>
                    <button
                        onClick={handleRefresh}
                        disabled={isLoading}
                        className="p-2 rounded-lg hover:bg-background-light transition-colors"
                    >
                        <RefreshCw className={`w-4 h-4 text-background-dark/50 ${isLoading ? 'animate-spin' : ''}`} />
                    </button>
                </div>

                {/* Days selector */}
                <div className="flex gap-1.5 sm:gap-2 mt-3 sm:mt-4 flex-wrap">
                    {[7, 14, 30, 60].map((d) => (
                        <button
                            key={d}
                            onClick={() => {
                                setDays(d);
                                void fetchPrediction(d, scenario);
                            }}
                            className={`px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                                days === d
                                    ? 'bg-primary text-white shadow-md'
                                    : 'bg-background-light text-background-dark/60 hover:bg-primary/10'
                            }`}
                        >
                            {d} {t('projection.days')}
                        </button>
                    ))}
                </div>

                {/* Scenario input */}
                <div className="mt-3 sm:mt-4 space-y-2">
                    <label className="text-xs font-bold text-background-dark/70 uppercase tracking-wide">
                        {t('projection.scenarioLabel')}
                    </label>
                    <div className="flex flex-col sm:flex-row gap-2">
                        <input
                            type="text"
                            value={scenario}
                            onChange={(e) => setScenario(e.target.value)}
                            onKeyDown={(e) => { if (e.key === 'Enter') handleAnalyze(); }}
                            placeholder={t('projection.scenarioPlaceholder')}
                            className="flex-1 px-3 py-2 rounded-lg border border-background-dark/10 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                        />
                        <button
                            onClick={handleAnalyze}
                            disabled={isLoading}
                            className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-bold hover:bg-primary/90 hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
                        >
                            {isLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                            {t('projection.analyze')}
                        </button>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 p-4 sm:p-6 overflow-y-auto">
                {error ? (
                    <div className="flex flex-col items-center justify-center h-full text-center">
                        <AlertTriangle className="w-12 h-12 text-orange-400 mb-3" />
                        <p className="text-sm text-background-dark/60">{error}</p>
                        <button onClick={handleRefresh} className="mt-4 px-4 py-2 bg-primary/10 text-primary rounded-lg text-sm font-medium">
                            {t('projection.retry')}
                        </button>
                    </div>
                ) : isLoading && !prediction ? (
                    <div className="flex flex-col items-center justify-center h-full">
                        <div className="w-8 h-8 border-3 border-primary/20 border-t-primary rounded-full animate-spin" />
                        <p className="mt-3 text-sm text-background-dark/60">{t('projection.loading')}</p>
                    </div>
                ) : prediction ? (
                    <div className="space-y-4 sm:space-y-5">
                        {/* Dual Avatar Comparison */}
                        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
                            {/* Current Avatar */}
                            <div className="text-center flex-1 w-full">
                                <span className="text-[10px] font-bold uppercase tracking-wider text-background-dark/40">{t('projection.today')}</span>
                                <div className="h-32 sm:h-40 w-full bg-gradient-to-b from-background-light/50 to-transparent rounded-2xl overflow-hidden">
                                    {renderAvatarPreview(currentScore, currentVitals)}
                                </div>
                                <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full mt-2 ${zoneColors[currentZone].badge} ${zoneColors[currentZone].border} border`}>
                                    <span className={`text-lg font-black ${zoneColors[currentZone].text}`}>{Math.round(prediction.current_score)}</span>
                                </div>
                                <p className={`text-xs font-medium mt-1 ${zoneColors[currentZone].text}`}>{prediction.current_risk_category}</p>
                            </div>

                            {/* Arrow */}
                            <div className="flex sm:flex-col items-center gap-1 px-2">
                                <ArrowRight className="w-6 h-6 text-background-dark/30 rotate-90 sm:rotate-0" />
                                <span className="text-[10px] font-bold text-background-dark/40">{days}d</span>
                            </div>

                            {/* Projected Avatar */}
                            <div className="text-center flex-1 w-full">
                                <span className="text-[10px] font-bold uppercase tracking-wider text-background-dark/40">{t('projection.projected')}</span>
                                <div className="h-32 sm:h-40 w-full bg-gradient-to-b from-background-light/50 to-transparent rounded-2xl overflow-hidden relative">
                                    <div className="absolute inset-0 bg-gradient-to-b from-purple-500/5 to-transparent pointer-events-none z-10" />
                                    <div className="absolute inset-0 opacity-20 pointer-events-none z-10"
                                         style={{ background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(147,51,234,0.1) 2px, rgba(147,51,234,0.1) 4px)' }} />
                                    {renderAvatarPreview(prediction.projected_score, projectedAvatarVitals, true)}
                                </div>
                                <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full mt-2 ${zoneColors[projectedZone].badge} ${zoneColors[projectedZone].border} border`}>
                                    <span className={`text-lg font-black ${zoneColors[projectedZone].text}`}>{Math.round(prediction.projected_score)}</span>
                                    {isImproving ? <TrendingUp className="w-4 h-4 text-emerald-500" /> : <TrendingDown className="w-4 h-4 text-rose-500" />}
                                </div>
                                <p className={`text-xs font-medium mt-1 ${zoneColors[projectedZone].text}`}>{prediction.projected_risk_category}</p>
                            </div>
                        </div>

                        {/* Score change summary */}
                        <div className={`p-3 rounded-2xl ${isImproving ? 'bg-emerald-50 border-emerald-200' : 'bg-rose-50 border-rose-200'} border`}>
                            <div className="flex items-center gap-3">
                                {isImproving ? <TrendingUp className="w-5 h-5 text-emerald-500 shrink-0" /> : <TrendingDown className="w-5 h-5 text-rose-500 shrink-0" />}
                                <div>
                                    <h4 className={`font-bold text-sm ${isImproving ? 'text-emerald-700' : 'text-rose-700'}`}>
                                        {isImproving ? t('projection.improving') : t('projection.declining')}
                                    </h4>
                                    <p className={`text-xs mt-0.5 ${isImproving ? 'text-emerald-600/80' : 'text-rose-600/80'}`}>
                                        Score {scoreChange > 0 ? '+' : ''}{scoreChange.toFixed(1)} pts &nbsp;·&nbsp; {prediction.current_risk_category} → {prediction.projected_risk_category}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Per-vital projected delta — only shown when a scenario was analysed */}
                        {hasScenarioAnalysis && delta && (
                            <div className="rounded-2xl border border-background-dark/8 overflow-hidden">
                                <div className="px-4 py-2.5 bg-background-light/60 border-b border-background-dark/8">
                                    <p className="text-[11px] font-black uppercase tracking-wide text-background-dark/50">Projected Vital Changes ({days}d)</p>
                                </div>
                                <div className="divide-y divide-background-dark/5">
                                    {[
                                        { icon: Heart, label: 'Heart Rate', key: 'bpm' as const, unit: ' bpm', isPositiveGood: false },
                                        { icon: Activity, label: 'HRV', key: 'hrv' as const, unit: ' ms', isPositiveGood: true },
                                        { icon: Droplets, label: 'SpO₂', key: 'spo2' as const, unit: '%', isPositiveGood: true },
                                        { icon: Thermometer, label: 'Temperature', key: 'temperature' as const, unit: '°C', isPositiveGood: false },
                                    ].map(({ icon: Icon, label, key, unit, isPositiveGood }) => {
                                        const curr = prediction.current_vitals?.[key];
                                        const proj = prediction.projected_vitals?.[key];
                                        const d = delta[key];
                                        return (
                                            <div key={key} className="flex items-center justify-between px-4 py-2.5">
                                                <div className="flex items-center gap-2">
                                                    <Icon className="w-3.5 h-3.5 text-background-dark/40" />
                                                    <span className="text-xs font-semibold text-background-dark/70">{label}</span>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    {curr !== undefined && (
                                                        <span className="text-xs text-background-dark/40 font-mono">{curr.toFixed(1)}{unit}</span>
                                                    )}
                                                    {proj !== undefined && (
                                                        <>
                                                            <ArrowRight className="w-3 h-3 text-background-dark/20" />
                                                            <span className="text-xs font-bold text-background-dark/70 font-mono">{proj.toFixed(1)}{unit}</span>
                                                        </>
                                                    )}
                                                    <DeltaBadge delta={d} unit={unit} isPositiveGood={isPositiveGood} />
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        {/* AI Review */}
                        {prediction.ai_review && (
                            <div className="rounded-2xl border border-purple-200/60 bg-gradient-to-br from-purple-50/80 to-white overflow-hidden">
                                <div className="px-4 py-2.5 bg-purple-100/50 border-b border-purple-200/60 flex items-center gap-2">
                                    <Sparkles className="w-3.5 h-3.5 text-purple-500" />
                                    <p className="text-[11px] font-black uppercase tracking-wide text-purple-700">AI Health Review</p>
                                </div>
                                <div className="px-4 py-3">
                                    <SimpleMarkdown text={prediction.ai_review} />
                                </div>
                            </div>
                        )}

                        {/* Scenario note (short summary when no full review) */}
                        {prediction.scenario_note && !prediction.ai_review && (
                            <div className="p-3 rounded-xl bg-purple-50 border border-purple-200">
                                <p className="text-xs text-purple-700 font-medium">💡 {prediction.scenario_note}</p>
                            </div>
                        )}

                        {/* Disclaimer */}
                        <p className="text-[10px] text-background-dark/40 text-center italic">{prediction.disclaimer}</p>
                    </div>
                ) : null}
            </div>
        </div>
    );
}
