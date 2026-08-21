import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { 
  Waves, 
  Lock, 
  Mail, 
  User,
  Building2,
  Briefcase,
  Layers,
  ArrowRight, 
  Globe, 
  AlertCircle,
  CheckCircle2,
  LogIn
} from 'lucide-react';
import { Button } from '../../components/ui/Button';

export const RegisterPage: React.FC = () => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [institution, setInstitution] = useState('Centre for Marine Living Resources & Ecology (CMLRE)');
  const [department, setDepartment] = useState('Ocean Hydrography & Marine Biology');
  const [designation, setDesignation] = useState('Research Scientist');

  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const { register } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password || !fullName) {
      setErrorMsg('Please complete all required fields.');
      return;
    }

    if (password !== confirmPassword) {
      setErrorMsg('Password confirmation does not match.');
      return;
    }

    setIsLoading(true);
    setErrorMsg(null);

    try {
      await register({
        email,
        password,
        fullName,
        institution,
        department,
        designation
      });
      addToast('success', 'Registration Successful', 'Welcome to CMLRE Marine Intelligence Platform.');
      navigate('/');
    } catch (err: any) {
      setErrorMsg(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-screen bg-marine-950 flex flex-col md:flex-row items-center justify-center p-4 sm:p-6 relative overflow-hidden">
      {/* Background Glows */}
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-ocean-cyan/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-ocean-teal/10 rounded-full blur-3xl pointer-events-none" />

      {/* Main Container */}
      <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-12 rounded-3xl glass-panel border border-marine-800 shadow-2xl overflow-hidden z-10 my-8">
        {/* Left Side: CMLRE Brand & Scientific Story */}
        <div className="md:col-span-5 p-8 sm:p-10 bg-gradient-to-br from-marine-900 via-marine-950 to-marine-950 flex flex-col justify-between border-b md:border-b-0 md:border-r border-marine-800">
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
                Researcher Onboarding & Institutional Access
              </h2>
              <p className="text-xs text-slate-300 leading-relaxed">
                Join the Indian Ocean unified marine intelligence ecosystem. Create your researcher profile to ingest datasets, analyze CTD profiles, access fisheries analytics, and run cross-domain scientific standardizations.
              </p>
            </div>

            {/* Scientific Pipeline Pill */}
            <div className="p-3.5 rounded-xl bg-marine-900/80 border border-marine-800 space-y-2.5">
              <div className="flex items-center gap-2 text-xs font-semibold text-ocean-teal">
                <Globe className="w-4 h-4" />
                <span>Verified Scientific Access</span>
              </div>
              <ul className="text-[11px] text-slate-400 space-y-1.5 font-sans">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                  <span>Darwin Core & CF Convention Quality Verification</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                  <span>PostGIS Spatial Indexing across EEZ Transects</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                  <span>Cross-Domain Data Fusion & Research Provenance</span>
                </li>
              </ul>
            </div>
          </div>

          <div className="pt-6 border-t border-marine-850 flex items-center justify-between text-[11px] text-slate-400">
            <span>Govt. of India • MoES</span>
            <span className="font-mono text-ocean-cyan">Kochi, Kerala</span>
          </div>
        </div>

        {/* Right Side: Registration Form */}
        <div className="md:col-span-7 p-8 sm:p-10 flex flex-col justify-center space-y-6 bg-marine-950/60">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-white">Create Researcher Account</h3>
              <p className="text-xs text-slate-400 mt-1">Register for institutional access to the Marine Platform.</p>
            </div>
            <Link
              to="/login"
              className="text-xs text-ocean-cyan hover:underline flex items-center gap-1 font-medium"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>Sign In</span>
            </Link>
          </div>

          {errorMsg && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-rose-950/50 border border-ocean-coral/40 text-ocean-coral text-xs">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          <form onSubmit={handleRegister} className="space-y-4">
            {/* Full Name */}
            <div className="space-y-1.5">
              <label htmlFor="register-fullName" className="text-xs font-medium text-slate-300">Full Name & Title</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  id="register-fullName"
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Dr. Rajesh Varma"
                  required
                  className="w-full bg-marine-900 border border-marine-700 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-ocean-cyan"
                />
              </div>
            </div>

            {/* Email */}
            <div className="space-y-1.5">
              <label htmlFor="register-email" className="text-xs font-medium text-slate-300">Institutional Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  id="register-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="r.varma@cmlre.gov.in"
                  required
                  className="w-full bg-marine-900 border border-marine-700 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-ocean-cyan font-mono"
                />
              </div>
            </div>

            {/* Institution & Department Row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label htmlFor="register-institution" className="text-xs font-medium text-slate-300">Institution</label>
                <div className="relative">
                  <Building2 className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    id="register-institution"
                    type="text"
                    value={institution}
                    onChange={(e) => setInstitution(e.target.value)}
                    placeholder="CMLRE / MoES / INCOIS"
                    className="w-full bg-marine-900 border border-marine-700 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-ocean-cyan"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label htmlFor="register-designation" className="text-xs font-medium text-slate-300">Designation / Role</label>
                <div className="relative">
                  <Briefcase className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    id="register-designation"
                    type="text"
                    value={designation}
                    onChange={(e) => setDesignation(e.target.value)}
                    placeholder="Senior Marine Scientist"
                    className="w-full bg-marine-900 border border-marine-700 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-ocean-cyan"
                  />
                </div>
              </div>
            </div>

            {/* Department */}
            <div className="space-y-1.5">
              <label htmlFor="register-department" className="text-xs font-medium text-slate-300">Division / Department</label>
              <div className="relative">
                <Layers className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  id="register-department"
                  type="text"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  placeholder="Ocean Hydrography & Modeling"
                  className="w-full bg-marine-900 border border-marine-700 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-ocean-cyan"
                />
              </div>
            </div>

            {/* Password & Confirm Password Row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label htmlFor="register-password" className="text-xs font-medium text-slate-300">Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    id="register-password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    required
                    className="w-full bg-marine-900 border border-marine-700 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-ocean-cyan font-mono"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label htmlFor="register-confirmPassword" className="text-xs font-medium text-slate-300">Confirm Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    id="register-confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••••••"
                    required
                    className="w-full bg-marine-900 border border-marine-700 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-ocean-cyan font-mono"
                  />
                </div>
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
              Register & Initialize Session
            </Button>
          </form>

          <div className="pt-3 border-t border-marine-800 text-center">
            <p className="text-xs text-slate-400">
              Already have an institutional account?{' '}
              <Link to="/login" className="text-ocean-cyan hover:underline font-medium">
                Sign In to Researcher Portal
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
