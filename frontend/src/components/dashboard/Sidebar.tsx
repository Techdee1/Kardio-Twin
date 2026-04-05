import { Settings, LayoutDashboard, LogOut, Calendar, BarChart3, ClipboardPen } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../../i18n/LanguageContext';

interface SidebarProps {
    activeView: 'overview' | 'projection' | 'history' | 'manual' | 'settings';
    setActiveView: (view: 'overview' | 'projection' | 'history' | 'manual' | 'settings') => void;
}

export default function Sidebar({ activeView, setActiveView }: SidebarProps) {
    const { t } = useLanguage();

    const navItems = [
        { id: 'overview', label: t('sidebar.overview'), icon: LayoutDashboard },
        { id: 'projection', label: t('sidebar.projection'), icon: Calendar },
        { id: 'history', label: t('sidebar.history'), icon: BarChart3 },
        { id: 'manual', label: t('sidebar.manual'), icon: ClipboardPen },
        { id: 'settings', label: t('sidebar.settings'), icon: Settings },
    ] as const;

    return (
        <>
            {/* Desktop sidebar */}
            <aside className="hidden md:flex w-64 h-[calc(100vh-4rem)] border-r border-primary/10 bg-white flex-col sticky top-16 shadow-[0_8px_30px_rgb(0,0,0,0.02)]">
                <div className="p-6 flex-1">
                    <nav className="space-y-2">
                        {navItems.map((item) => {
                            const Icon = item.icon;
                            const isActive = activeView === item.id;

                            return (
                                <button
                                    key={item.id}
                                    onClick={() => setActiveView(item.id)}
                                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${isActive
                                        ? 'bg-primary/10 text-primary font-bold shadow-sm border border-primary/20'
                                        : 'text-background-dark/60 hover:text-background-dark hover:bg-background-light font-medium'
                                        }`}
                                >
                                    <Icon className={`w-5 h-5 ${isActive ? 'text-primary' : ''}`} />
                                    {item.label}
                                </button>
                            );
                        })}
                    </nav>
                </div>

                <div className="p-6 border-t border-primary/10 bg-background-light/50">
                    <Link to="/" className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-rose-500 hover:bg-rose-50 hover:shadow-sm transition-all font-medium border border-transparent hover:border-rose-100">
                        <LogOut className="w-5 h-5" />
                        <span>{t('sidebar.exit')}</span>
                    </Link>
                </div>
            </aside>

            {/* Mobile bottom tab bar */}
            <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-t border-primary/10 shadow-[0_-4px_20px_rgb(0,0,0,0.05)]">
                <div className="flex items-center justify-around px-2 py-1">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = activeView === item.id;

                        return (
                            <button
                                key={item.id}
                                onClick={() => setActiveView(item.id)}
                                className={`flex flex-col items-center gap-0.5 px-3 py-2 rounded-xl transition-all duration-200 min-w-[60px] ${isActive
                                    ? 'text-primary'
                                    : 'text-background-dark/40'
                                    }`}
                            >
                                <Icon className={`w-5 h-5 ${isActive ? 'text-primary' : ''}`} />
                                <span className={`text-[10px] ${isActive ? 'font-bold' : 'font-medium'}`}>{item.label}</span>
                            </button>
                        );
                    })}
                    <Link
                        to="/"
                        className="flex flex-col items-center gap-0.5 px-3 py-2 rounded-xl text-rose-400 min-w-[60px]"
                    >
                        <LogOut className="w-5 h-5" />
                        <span className="text-[10px] font-medium">{t('sidebar.exit')}</span>
                    </Link>
                </div>
            </nav>
        </>
    );
}
