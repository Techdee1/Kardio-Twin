import { Settings, LayoutDashboard, LogOut, Calendar, BarChart3 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../../i18n/LanguageContext';

interface SidebarProps {
    activeView: 'overview' | 'projection' | 'history' | 'settings';
    setActiveView: (view: 'overview' | 'projection' | 'history' | 'settings') => void;
}

export default function Sidebar({ activeView, setActiveView }: SidebarProps) {
    const { t } = useLanguage();

    const navItems = [
        { id: 'overview', label: t('sidebar.overview'), icon: LayoutDashboard },
        { id: 'projection', label: t('sidebar.projection'), icon: Calendar },
        { id: 'history', label: t('sidebar.history'), icon: BarChart3 },
        { id: 'settings', label: t('sidebar.settings'), icon: Settings },
    ] as const;

    return (
        <aside className="w-64 h-[calc(100vh-4rem)] border-r border-primary/10 bg-white flex flex-col sticky top-16 shadow-[0_8px_30px_rgb(0,0,0,0.02)]">
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
    );
}
