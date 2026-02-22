import { useState, useEffect } from 'react';
import { Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { BarChart3, RefreshCw, AlertTriangle, Clock } from 'lucide-react';
import { api } from '../../services/api';
import type { HistoryEntry } from '../../services/api';
import { useLanguage } from '../../i18n/LanguageContext';

interface HistoryChartProps {
    sessionId: string;
}

const zoneColors: Record<string, string> = {
    GREEN: '#10b981',
    YELLOW: '#f59e0b',
    ORANGE: '#f97316',
    RED: '#ef4444',
};

interface ChartDataPoint {
    time: string;
    score: number;
    zone: string;
    heartRate: number;
    hrv: number;
    spo2: number;
    temperature: number;
}

export default function HistoryChart({ sessionId }: HistoryChartProps) {
    const [history, setHistory] = useState<ChartDataPoint[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedMetric, setSelectedMetric] = useState<'score' | 'heartRate' | 'hrv' | 'spo2'>('score');
    const { t } = useLanguage();

    const fetchHistory = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await api.getHistory(sessionId);
            const chartData: ChartDataPoint[] = data.map((entry: HistoryEntry) => ({
                time: new Date(entry.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                score: Math.round(entry.score),
                zone: entry.zone,
                heartRate: Math.round(entry.components.heart_rate.value),
                hrv: Math.round(entry.components.hrv.value),
                spo2: Math.round(entry.components.spo2.value),
                temperature: entry.components.temperature.value,
            }));
            setHistory(chartData);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch history');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchHistory();
        // Refresh every 10 seconds
        const interval = setInterval(fetchHistory, 10000);
        return () => clearInterval(interval);
    }, [sessionId]);

    const metrics = [
        { key: 'score', label: t('history.score'), color: '#6366f1', unit: '' },
        { key: 'heartRate', label: t('history.heartRate'), color: '#ef4444', unit: 'bpm' },
        { key: 'hrv', label: t('history.hrv'), color: '#8b5cf6', unit: 'ms' },
        { key: 'spo2', label: t('history.spo2'), color: '#3b82f6', unit: '%' },
    ] as const;

    const activeMetric = metrics.find(m => m.key === selectedMetric)!;

    // Custom tooltip
    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload as ChartDataPoint;
            return (
                <div className="bg-white/95 backdrop-blur-md p-3 rounded-xl shadow-lg border border-primary/10">
                    <p className="text-xs font-bold text-background-dark/60 mb-2">{label}</p>
                    <div className="space-y-1">
                        <p className="text-sm">
                            <span className="font-medium text-background-dark/70">{t('history.score')}:</span>{' '}
                            <span className="font-bold" style={{ color: zoneColors[data.zone] }}>{data.score}</span>
                        </p>
                        <p className="text-sm">
                            <span className="font-medium text-background-dark/70">❤️:</span>{' '}
                            <span className="font-bold">{data.heartRate} bpm</span>
                        </p>
                        <p className="text-sm">
                            <span className="font-medium text-background-dark/70">HRV:</span>{' '}
                            <span className="font-bold">{data.hrv} ms</span>
                        </p>
                        <p className="text-sm">
                            <span className="font-medium text-background-dark/70">SpO₂:</span>{' '}
                            <span className="font-bold">{data.spo2}%</span>
                        </p>
                    </div>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="h-full flex flex-col bg-white/80 backdrop-blur-md rounded-3xl border border-primary/10 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-background-dark/5">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-indigo-100 border border-indigo-200">
                            <BarChart3 className="w-5 h-5 text-indigo-600" />
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-background-dark">{t('history.title')}</h3>
                            <p className="text-xs text-background-dark/60 flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {t('history.subtitle')}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={fetchHistory}
                        disabled={isLoading}
                        className="p-2 rounded-lg hover:bg-background-light transition-colors"
                    >
                        <RefreshCw className={`w-4 h-4 text-background-dark/50 ${isLoading ? 'animate-spin' : ''}`} />
                    </button>
                </div>

                {/* Metric selector */}
                <div className="flex gap-2 mt-4 flex-wrap">
                    {metrics.map((metric) => (
                        <button
                            key={metric.key}
                            onClick={() => setSelectedMetric(metric.key)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                                selectedMetric === metric.key
                                    ? 'text-white shadow-md'
                                    : 'bg-background-light text-background-dark/60 hover:bg-primary/10'
                            }`}
                            style={{
                                backgroundColor: selectedMetric === metric.key ? metric.color : undefined,
                            }}
                        >
                            {metric.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Chart */}
            <div className="flex-1 p-4">
                {error ? (
                    <div className="flex flex-col items-center justify-center h-full text-center">
                        <AlertTriangle className="w-12 h-12 text-orange-400 mb-3" />
                        <p className="text-sm text-background-dark/60">{error}</p>
                        <button
                            onClick={fetchHistory}
                            className="mt-4 px-4 py-2 bg-primary/10 text-primary rounded-lg text-sm font-medium"
                        >
                            {t('history.retry')}
                        </button>
                    </div>
                ) : isLoading && history.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full">
                        <div className="w-8 h-8 border-3 border-primary/20 border-t-primary rounded-full animate-spin" />
                        <p className="mt-3 text-sm text-background-dark/60">{t('history.loading')}</p>
                    </div>
                ) : history.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-center">
                        <BarChart3 className="w-12 h-12 text-background-dark/20 mb-3" />
                        <p className="text-sm text-background-dark/60">{t('history.noData')}</p>
                        <p className="text-xs text-background-dark/40 mt-1">{t('history.noDataHint')}</p>
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                            <defs>
                                <linearGradient id={`gradient-${selectedMetric}`} x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={activeMetric.color} stopOpacity={0.3} />
                                    <stop offset="95%" stopColor={activeMetric.color} stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                            <XAxis 
                                dataKey="time" 
                                tick={{ fontSize: 10, fill: '#9ca3af' }}
                                tickLine={false}
                                axisLine={{ stroke: '#e5e7eb' }}
                            />
                            <YAxis 
                                tick={{ fontSize: 10, fill: '#9ca3af' }}
                                tickLine={false}
                                axisLine={false}
                                domain={selectedMetric === 'score' ? [0, 100] : ['auto', 'auto']}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <Area
                                type="monotone"
                                dataKey={selectedMetric}
                                stroke={activeMetric.color}
                                strokeWidth={2}
                                fill={`url(#gradient-${selectedMetric})`}
                                dot={{ fill: activeMetric.color, strokeWidth: 0, r: 3 }}
                                activeDot={{ fill: activeMetric.color, strokeWidth: 2, stroke: '#fff', r: 5 }}
                            />
                            {/* Zone threshold lines for score */}
                            {selectedMetric === 'score' && (
                                <>
                                    <Line type="monotone" dataKey={() => 80} stroke="#10b981" strokeDasharray="5 5" dot={false} strokeWidth={1} />
                                    <Line type="monotone" dataKey={() => 55} stroke="#f59e0b" strokeDasharray="5 5" dot={false} strokeWidth={1} />
                                    <Line type="monotone" dataKey={() => 30} stroke="#ef4444" strokeDasharray="5 5" dot={false} strokeWidth={1} />
                                </>
                            )}
                        </AreaChart>
                    </ResponsiveContainer>
                )}
            </div>

            {/* Legend for score zones */}
            {selectedMetric === 'score' && history.length > 0 && (
                <div className="px-6 pb-4 flex justify-center gap-4">
                    {[
                        { label: t('history.zoneGreen'), color: '#10b981', threshold: '≥80' },
                        { label: t('history.zoneYellow'), color: '#f59e0b', threshold: '55-79' },
                        { label: t('history.zoneOrange'), color: '#f97316', threshold: '30-54' },
                        { label: t('history.zoneRed'), color: '#ef4444', threshold: '<30' },
                    ].map((zone) => (
                        <div key={zone.label} className="flex items-center gap-1.5">
                            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: zone.color }} />
                            <span className="text-[10px] text-background-dark/50">{zone.threshold}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
