import React, { useEffect, useState, useRef } from 'react';
import './OceaNixIntro.css';

interface OceaNixIntroOverlayProps {
  onFinish?: () => void;
}

export const OceaNixIntroOverlay: React.FC<OceaNixIntroOverlayProps> = ({ onFinish }) => {
  const [isFadingOut, setIsFadingOut] = useState(false);
  const [isDone, setIsDone] = useState(false);
  const timerRef = useRef<number | null>(null);
  const fadeTimerRef = useRef<number | null>(null);

  useEffect(() => {
    // At 2650ms (2.65s), start the subtle 350ms opacity dissolve into the dashboard
    fadeTimerRef.current = window.setTimeout(() => {
      setIsFadingOut(true);
    }, 2650);

    // At exactly 3000ms (3.0s), fully finish and unmount overlay
    timerRef.current = window.setTimeout(() => {
      setIsDone(true);
      onFinish?.();
    }, 3000);

    return () => {
      if (fadeTimerRef.current) clearTimeout(fadeTimerRef.current);
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [onFinish]);

  if (isDone) return null;

  return (
    <div
      className={`oceanix-startup-overlay ${isFadingOut ? 'oceanix-overlay-fade-out' : ''}`}
      aria-label="OceaNix Startup Intro"
      role="presentation"
    >
      {/* Background Atmosphere - Exact CMLRE marine navy and subtle glows */}
      <div className="absolute inset-0 oceanix-bg-ambient pointer-events-none" />
      <div className="absolute inset-0 oceanix-subtle-grid pointer-events-none opacity-40" />
      <div className="absolute inset-0 oceanix-vignette pointer-events-none" />

      {/* Subtle Top Ambient Light Ray */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[300px] bg-gradient-to-b from-ocean-cyan/5 via-ocean-teal/2 to-transparent blur-3xl pointer-events-none" />

      {/* Center Cinematic Typography Stage */}
      <div className="relative z-10 flex flex-col items-center justify-center w-full max-w-5xl px-6">
        {/* Phase 1: 0.0s – 1.0s: “Introducing” */}
        <div className="absolute flex items-center justify-center text-center">
          <span className="oceanix-anim-introducing text-sm sm:text-base md:text-lg lg:text-xl font-medium tracking-[0.32em] uppercase text-slate-300 drop-shadow-[0_0_12px_rgba(0,240,255,0.25)] select-none">
            Introducing
          </span>
        </div>

        {/* Phase 2: 1.0s – 3.0s: “OceaNix” */}
        <div className="relative flex flex-col items-center justify-center">
          {/* Synchronized Oceanic Radial Back-Glow */}
          <div className="absolute w-72 h-72 sm:w-96 sm:h-96 md:w-[520px] md:h-[280px] bg-gradient-to-r from-ocean-cyan/20 via-blue-600/15 to-ocean-teal/20 rounded-full blur-3xl oceanix-glow-bloom pointer-events-none" />

          {/* Hero Typography */}
          <div className="relative overflow-hidden px-4 py-2 flex items-center justify-center">
            <h1 className="oceanix-anim-brand text-5xl sm:text-7xl md:text-8xl lg:text-9xl font-extrabold tracking-[-0.035em] font-sans select-none leading-none">
              <span className="oceanix-text-gradient drop-shadow-[0_0_35px_rgba(0,240,255,0.45)]">
                OceaNix
              </span>
            </h1>

            {/* Horizontal Light Sweep Sheen */}
            <div className="oceanix-light-sweep" />
          </div>

          {/* Minimal Oceanic Horizon Reflection Line */}
          <div className="w-48 sm:w-72 md:w-96 h-[1.5px] bg-gradient-to-r from-transparent via-ocean-cyan/60 to-transparent oceanix-horizon-line mt-3 sm:mt-5 rounded-full" />
        </div>
      </div>
    </div>
  );
};
export default OceaNixIntroOverlay;
