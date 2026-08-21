import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { 
  Waves, 
  ShieldCheck, 
  Lock, 
  Mail, 
  ArrowRight, 
  FlaskConical, 
  Globe, 
  Cpu, 
  AlertCircle,
  UserPlus
} from 'lucide-react';
import { Button } from '../../components/ui/Button';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('test_scientist_99@cmlre.gov.in');
  const [password, setPassword] = useState('TestPassword123!');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const { login } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setErrorMsg('Please provide both official email and security token.');
      return;
    }

    setIsLoading(true);
    setErrorMsg(null);
    try {
      await login(email, password);
      addToast('success', 'Authentication Successful', 'Welcome to CMLRE Marine Intelligence Platform.');
      navigate('/');
    } catch (err: any) {
      setErrorMsg(err.message || 'Invalid credentials. Please verify your CMLRE access token.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickDemoLogin = async (type: 'scientist' | 'admin') => {
    const creds = type === 'admin'
      ? { email: 'admin@cmlre.gov.in', pass: 'moes-admin-2026' }
      : { email: 'test_scientist_99@cmlre.gov.in', pass: 'TestPassword123!' };

    setEmail(creds.email);
    setPassword(creds.pass);
    setIsLoading(true);
    setErrorMsg(null);
    try {
      await login(creds.email, creds.pass);
      addToast('success', 'Logged in as ' + (type === 'admin' ? 'MoES Administrator' : 'Marine Scientist'));
      navigate('/');
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-screen bg-marine-950 flex flex-col md:flex-row items-center justify-center p-6 relative overflow-hidden">
      {/* Background Glows */}
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-ocean-cyan/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-ocean-teal/10 rounded-full blur-3xl pointer-events-none" />

      {/* Main Container */}
      <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 rounded-3xl glass-panel border border-marine-800 shadow-2xl overflow-hidden z-10">
        {/* Left Side: CMLRE Brand & Scientific Story */}
        <div className="p-8 sm:p-10 bg-gradient-to-br from-marine-900 via-marine-950 to-marine-950 flex flex-col justify-between border-b md:border-b-0 md:border-r border-marine-800">
          <div className="space-y-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-ocean-cyan to-blue-600 p-[2px] shadow-glow-cyan">
                <div className="w-full h-full bg-marine-950 rounded-[14px] flex items-center justify-center">
                  <Waves className="w-6 h-6 text-ocean-cyan animate-pulse-subtle" />
                </div>
              </div>
              <div>
                <h1 className="text-lg font-bold text-white tracking-wider">CMLRE</h1>
                <p className="text-xs text-ocean-cyan font-mono font-medium">Ministry of Earth Sciences</p>
              </div>
            </div>

            <div className="space-y-3">
              <h2 className="text-xl font-bold text-white leading-tight">
                AI-Driven Unified Marine Intelligence Platform
              </h2>
              <p className="text-xs text-slate-300 leading-relaxed">
                Centralized scientific workspace uniting oceanographic hydrography, commercial fisheries CPUE, Darwin Core biodiversity, and high-throughput molecular eDNA records across the Indian Ocean.
              </p>
            </div>

            {/* Scientific Pipeline Pill */}
            <div className="p-3.5 rounded-xl bg-marine-900/80 border border-marine-800 space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-ocean-teal">
                <Globe className="w-4 h-4" />
                <span>Standardized Data Fusion Architecture</span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono">
                TXT/CSV Ingestion → Quality Control → PostGIS Spatial Indexing → Cross-Domain ML Insights
              </p>
            </div>
          </div>

          <div className="pt-6 border-t border-marine-850 flex items-center justify-between text-[11px] text-slate-400">
            <span>Govt. of India • MoES</span>
            <span className="font-mono text-ocean-cyan">Kochi, Kerala</span>
          </div>
        </div>

        {/* Right Side: Auth Form */}
        <div className="p-8 sm:p-10 flex flex-col justify-center space-y-6 bg-marine-950/60">
          <div>
            <h3 className="text-lg font-bold text-white">Researcher Portal Sign In</h3>
            <p className="text-xs text-slate-400 mt-1">Authenticate with your CMLRE institutional account or Supabase JWT.</p>
          </div>

          {errorMsg && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-rose-950/50 border border-ocean-coral/40 text-ocean-coral text-xs">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Institutional Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="scientist@cmlre.gov.in"
                  required
                  className="w-full bg-marine-900 border border-marine-700 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-ocean-cyan font-mono"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Security Token / Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  className="w-full bg-marine-900 border border-marine-700 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-ocean-cyan font-mono"
                />
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={isLoading}
              rightIcon={<ArrowRight className="w-4 h-4" />}
              className="w-full mt-2"
            >
              Authenticate CMLRE Session
            </Button>
          </form>

          <div className="text-center pt-1">
            <p className="text-xs text-slate-400">
              New to the platform?{' '}
              <Link to="/register" className="text-ocean-cyan hover:underline font-medium inline-flex items-center gap-1">
                <UserPlus className="w-3 h-3" />
                <span>Create Researcher Account</span>
              </Link>
            </p>
          </div>

          {/* Quick Demo Access Buttons */}
          <div className="space-y-2 pt-2 border-t border-marine-800">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-semibold text-center">
              Quick Hackathon Demo Login
            </span>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleQuickDemoLogin('scientist')}
                className="p-2 rounded-lg bg-marine-900 hover:bg-marine-850 border border-marine-700 hover:border-ocean-cyan text-xs text-slate-200 transition-all text-center flex items-center justify-center gap-1.5"
              >
                <FlaskConical className="w-3.5 h-3.5 text-ocean-cyan" />
                <span>Marine Scientist</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickDemoLogin('admin')}
                className="p-2 rounded-lg bg-marine-900 hover:bg-marine-850 border border-marine-700 hover:border-ocean-amber text-xs text-slate-200 transition-all text-center flex items-center justify-center gap-1.5"
              >
                <ShieldCheck className="w-3.5 h-3.5 text-ocean-amber" />
                <span>MoES Admin</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
