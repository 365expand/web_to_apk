'use client';

import React, { useState, useEffect } from 'react';
import { Wifi, Battery, Signal, Loader2 } from 'lucide-react';

interface PhoneMockupProps {
  appName: string;
  websiteUrl: string;
  iconPreviewUrl: string | null;
}

export default function PhoneMockup({ websiteUrl }: PhoneMockupProps) {
  // Format URL nicely for iframe
  const rawUrl = websiteUrl.trim();
  const formattedUrl = rawUrl
    ? (rawUrl.startsWith('http://') || rawUrl.startsWith('https://') ? rawUrl : `https://${rawUrl}`)
    : 'https://example.com';

  const [isLoading, setIsLoading] = useState(true);
  const [iframeKey, setIframeKey] = useState(0);
  const [time, setTime] = useState('09:41');

  // Realistic dynamic device clock
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false }));
    };
    updateTime();
    const interval = setInterval(updateTime, 30000);
    return () => clearInterval(interval);
  }, []);

  // When url changes, reload iframe and show loading indicator
  useEffect(() => {
    setIsLoading(true);
    setIframeKey(k => k + 1);
  }, [formattedUrl]);

  return (
    <div className="flex flex-col items-center w-full max-w-[310px] mx-auto select-none">
      {/* Outer Phone Hardware Chassis - Clean seamless flagship frame */}
      <div className="relative w-full aspect-[9/19] bg-slate-950 rounded-[46px] p-2.5 shadow-[0_20px_50px_rgba(15,23,42,0.35),0_0_0_1px_rgba(255,255,255,0.08)] ring-1 ring-slate-800/80">
        
        {/* Inner Screen Frame with concentric matching radius */}
        <div className="relative w-full h-full bg-white rounded-[38px] overflow-hidden flex flex-col shadow-inner">
          
          {/* Android Status Bar */}
          <div className="h-7 bg-slate-950 text-white px-5 flex items-center justify-between text-[11px] font-semibold tracking-tight z-20 flex-shrink-0 select-none">
            {/* Clock */}
            <span className="font-medium text-slate-300 text-[11px] w-12 text-left">{time}</span>

            {/* Center Punch-Hole Camera */}
            <div className="w-3.5 h-3.5 rounded-full bg-black border border-slate-800 flex items-center justify-center flex-shrink-0">
              <div className="w-1.5 h-1.5 rounded-full bg-indigo-950/80"></div>
            </div>

            {/* System Status Icons */}
            <div className="flex items-center justify-end space-x-1.5 text-slate-300 w-12">
              <span className="text-[9px] font-bold text-slate-400">5G</span>
              <Signal className="w-3 h-3 text-slate-300" />
              <Wifi className="w-3 h-3 text-slate-300" />
              <Battery className="w-3.5 h-3.5 text-slate-300 fill-slate-300" />
            </div>
          </div>

          {/* Full Screen Edge-to-Edge Web App Display */}
          <div className="flex-1 w-full bg-white relative overflow-hidden">
            {isLoading && (
              <div className="absolute inset-0 bg-white/90 backdrop-blur-[1px] flex flex-col items-center justify-center z-10 transition-opacity">
                <Loader2 className="w-6 h-6 text-indigo-600 animate-spin mb-2" />
                <span className="text-[11px] font-medium text-slate-500">Opening app...</span>
              </div>
            )}
            <iframe
              key={iframeKey}
              src={formattedUrl}
              title="Android Native App Screen"
              className="w-full h-full border-0 block bg-white"
              sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
              onLoad={() => setIsLoading(false)}
            />

            {/* Floating Android Gesture Navigation Pill (Edge-to-Edge overlay) */}
            <div className="absolute bottom-2 left-1/2 -translate-x-1/2 w-28 h-1 bg-slate-900/40 backdrop-blur-sm rounded-full pointer-events-none z-20"></div>
          </div>

        </div>
      </div>

      <div className="mt-3 flex items-center space-x-1.5 text-[11px] text-slate-500 font-medium">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
        <span>Live Android App View</span>
      </div>
    </div>
  );
}
