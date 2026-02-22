import { useState, useEffect, Suspense } from 'react';
import { TrendingDown, TrendingUp, AlertTriangle, ArrowRight, RefreshCw, Calendar } from 'lucide-react';
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

export default function ProjectionPanel({ sessionId, currentScore, currentVitals }: ProjectionPanelProps) {
    const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [days, setDays] = useState(30);
    const { t } = useLanguage();

    const fetchPrediction = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await api.getPrediction({ session_id: sessionId, days });
            setPrediction(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch prediction');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchPrediction();
    }, [sessionId, days]);

    const currentZone = zoneFromScore(currentScore);
    const projectedZone = prediction ? zoneFromScore(prediction.projected_score) : 'GREEN';
    const scoreChange = prediction ? prediction.projected_score - prediction.current_score : 0;
    const isImproving = scoreChange >= 0;

    return (
        <div className="h-full flex flex-col bg-white/80 backdrop-blur-md rounded-3xl border border-primary/10 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-background-dark/5">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-purple-100 border border-purple-200">
                            <Calendar className="w-5 h-5 text-purple-600" />
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-background-dark">{t('projection.title')}</h3>
                            <p className="text-xs text-background-dark/60">{t('projection.subtitle')}</p>
                        </div>
                    </div>
                    <button
                        onClick={fetchPrediction}
                        disabled={isLoading}
                        className="p-2 rounded-lg hover:bg-background-light transition-colors"
                    >
                        <RefreshCw className={`w-4 h-4 text-background-dark/50 ${isLoading ? 'animate-spin' : ''}`} />
                    </button>
                </div>

                {/* Days selector */}
                <div className="flex gap-2 mt-4">
                    {[7, 14, 30, 60].map((d) => (
                        <button
                            key={d}
                            onClick={() => setDays(d)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                                days === d
                                    ? 'bg-primary text-white shadow-md'
                                    : 'bg-background-light text-background-dark/60 hover:bg-primary/10'
                            }`}
                        >
                            {d} {t('projection.days')}
                        </button>
                    ))}
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 p-6 overflow-y-auto">
                {error ? (
                    <div className="flex flex-col items-center justify-center h-full text-center">
                        <AlertTriangle className="w-12 h-12 text-orange-400 mb-3" />
                        <p className="text-sm text-background-dark/60">{error}</p>
                        <button
                            onClick={fetchPrediction}
                            className="mt-4 px-4 py-2 bg-primary/10 text-primary rounded-lg text-sm font-medium"
                        >
                            {t('projection.retry')}
                        </button>
                    </div>
                ) : isLoading && !prediction ? (
                    <div className="flex flex-col items-center justify-center h-full">
                        <div className="w-8 h-8 border-3 border-primary/20 border-t-primary rounded-full animate-spin" />
                        <p className="mt-3 text-sm text-background-dark/60">{t('projection.loading')}</p>
                    </div>
                ) : prediction ? (
                    <div className="space-y-6">
                        {/* Dual Avatar Comparison */}
                        <div className="flex items-center justify-center gap-4">
                            {/* Current Avatar */}
                            <div className="text-center flex-1">
                                <span className="text-[10px] font-bold uppercase tracking-wider text-background-dark/40">
                                    {t('projection.today')}
                                </span>
                                <div className="h-40 w-full bg-gradient-to-b from-background-light/50 to-transparent rounded-2xl overflow-hidden">
                                    <Canvas camera={{ position: [0, 0, 3], fov: 50 }}>
                                        <Suspense fallback={null}>
                                            <ambientLight intensity={0.5} />
                                            <directionalLight position={[5, 5, 5]} intensity={1} />
                                            <Environment preset="city" />
                                            <HealthAvatar 
                                                score={currentScore} 
                                                vitals={currentVitals}
                                            />
                                            <OrbitControls enablePan={false} enableZoom={false} />
                                        </Suspense>
                                    </Canvas>
                                </div>
                                <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full mt-2 ${zoneColors[currentZone].badge} ${zoneColors[currentZone].border} border`}>
                                    <span className={`text-lg font-black ${zoneColors[currentZone].text}`}>
                                        {Math.round(prediction.current_score)}
                                    </span>
                                </div>
                                <p className={`text-xs font-medium mt-1 ${zoneColors[currentZone].text}`}>
                                    {prediction.current_risk_category}
                                </p>
                            </div>

                            {/* Arrow */}
                            <div className="flex flex-col items-center gap-1 px-2">
                                <ArrowRight className="w-6 h-6 text-background-dark/30" />
                                <span className="text-[10px] font-bold text-background-dark/40">
                                    {days}d
                                </span>
                            </div>

                            {/* Projected Avatar */}
                            <div className="text-center flex-1">
                                <span className="text-[10px] font-bold uppercase tracking-wider text-background-dark/40">
                                    {t('projection.projected')}
                                </span>
                                <div className="h-40 w-full bg-gradient-to-b from-background-light/50 to-transparent rounded-2xl overflow-hidden relative">
                                    {/* Hologram overlay effect */}
                                    <div className="absolute inset-0 bg-gradient-to-b from-purple-500/5 to-transparent pointer-events-none z-10" />
                                    <div className="absolute inset-0 opacity-20 pointer-events-none z-10" 
                                         style={{ 
                                             background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(147,51,234,0.1) 2px, rgba(147,51,234,0.1) 4px)' 
                                         }} 
                                    />
                                    <Canvas camera={{ position: [0, 0, 3], fov: 50 }}>
                                        <Suspense fallback={null}>
                                            <ambientLight intensity={0.4} />
                                            <directionalLight position={[5, 5, 5]} intensity={0.8} />
                                            <Environment preset="city" />
                                            <HealthAvatar 
                                                score={prediction.projected_score} 
                                                vitals={currentVitals}
                                            />
                                            <OrbitControls enablePan={false} enableZoom={false} />
                                        </Suspense>
                                    </Canvas>
                                </div>
                                <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full mt-2 ${zoneColors[projectedZone].badge} ${zoneColors[projectedZone].border} border`}>
                                    <span className={`text-lg font-black ${zoneColors[projectedZone].text}`}>
                                        {Math.round(prediction.projected_score)}
                                    </span>
                                    {isImproving ? (
                                        <TrendingUp className="w-4 h-4 text-emerald-500" />
                                    ) : (
                                        <TrendingDown className="w-4 h-4 text-rose-500" />
                                    )}
                                </div>
                                <p className={`text-xs font-medium mt-1 ${zoneColors[projectedZone].text}`}>
                                    {prediction.projected_risk_category}
                                </p>
                            </div>
                        </div>

                        {/* Change Summary */}
                        <div className={`p-4 rounded-2xl ${isImproving ? 'bg-emerald-50 border-emerald-200' : 'bg-rose-50 border-rose-200'} border`}>
                            <div className="flex items-start gap-3">
                                {isImproving ? (
                                    <TrendingUp className="w-5 h-5 text-emerald-500 mt-0.5" />
                                ) : (
                                    <TrendingDown className="w-5 h-5 text-rose-500 mt-0.5" />
                                )}
                                <div>
                                    <h4 className={`font-bold text-sm ${isImproving ? 'text-emerald-700' : 'text-rose-700'}`}>
                                        {isImproving ? t('projection.improving') : t('projection.declining')}
                                    </h4>
                                    <ul className="mt-2 space-y-1 text-xs text-background-dark/70">
                                        <li>• {t('projection.scoreChange')}: {scoreChange > 0 ? '+' : ''}{scoreChange.toFixed(1)}</li>
                                        <li>• {t('projection.hrChange')}: +{prediction.projected_resting_hr_increase_bpm.toFixed(1)} bpm</li>
                                        <li>• {t('projection.riskChange')}: {prediction.current_risk_category} → {prediction.projected_risk_category}</li>
                                    </ul>
                                </div>
                            </div>
                        </div>

                        {/* Disclaimer */}
                        <p className="text-[10px] text-background-dark/40 text-center italic">
                            {prediction.disclaimer}
                        </p>
                    </div>
                ) : null}
            </div>
        </div>
    );
}
