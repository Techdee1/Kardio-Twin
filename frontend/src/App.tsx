import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';
import LandingPage from './pages/LandingPage';
import DashboardPage from './pages/DashboardPage';
import DemoPage from './pages/DemoPage';
import { useEffect } from 'react';
import { LanguageProvider } from './i18n/LanguageContext';

function App() {
  useEffect(() => {
    document.documentElement.classList.add('dark');
  }, []);

  return (
    <LanguageProvider>
      <Router>
        <div className="bg-background-light dark:bg-background-dark text-slate-900 dark:text-slate-100 min-h-screen font-display transition-colors duration-300 overflow-x-hidden">
          <Routes>
            <Route path="/" element={
              <>
                <Navbar />
                <LandingPage />
                <Footer />
              </>
            } />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/demo" element={<DemoPage />} />
          </Routes>
        </div>
      </Router>
    </LanguageProvider>
  );
}

export default App;
