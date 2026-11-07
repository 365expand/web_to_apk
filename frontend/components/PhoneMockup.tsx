'use client';

import React, { useState, useEffect } from 'react';
import { Wifi, Battery, Signal } from 'lucide-react';

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
  const [time, setTime] = useState('10:24');

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

  // When url changes, reload iframe and show native loading bar
  useEffect(() => {
    setIsLoading(true);
    setIframeKey(k => k + 1);
  }, [formattedUrl]);

  return (
    <div className="flex flex-col items-center w-full max-w-[330px] mx-auto select-none">
      {/* Outer Phone Hardware Chassis with side buttons */}
      <div className="relative w-full aspect-[9/19.5] bg-slate-900 rounded-[50px] p-3 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.5),0_0_0_1px_rgba(255,255,255,0.1)] ring-1 ring-slate-800">
        
        {/* Left Side Buttons (Volume Rocker) */}
        <div className="absolute -left-[3px] top-28 w-[3px] h-10 bg-slate-700 rounded-l-sm"></div>
        <div className="absolute -left-[3px] top-42 w-[3px] h-10 bg-slate-700 rounded-l-sm"></div>
        
        {/* Right Side Button (Power Button) */}
        <div className="absolute -right-[3px] top-32 w-[3px] h-14 bg-slate-700 rounded-r-sm"></div>

        {/* Inner Phone Screen Frame */}
        <div className="relative w-full h-full bg-black rounded-[40px] overflow-hidden flex flex-col shadow-inner">
          
          {/* Android Status Bar with Punch Hole Camera */}
          <div className="relative h-7 bg-black text-white px-5 flex items-center justify-between text-[11px] font-semibold tracking-tight z-30 select-none">
            {/* Clock */}
            <span className="font-medium text-slate-200 pl-1 text-[11px]">{time}</span>

            {/* Center Punch-Hole Front Camera */}
            <div className="absolute left-1/2 -translate-x-1/2 top-1.5 w-3.5 h-3.5 rounded-full bg-black border border-slate-800 flex items-center justify-center">
              <div className="w-1.5 h-1.5 rounded-full bg-[#0a1226] border border-blue-950"></div>
            </div>

            {/* System Status Icons (5G, Signal, Wifi, Battery) */}
            <div className="flex items-center space-x-1.5 text-slate-200 pr-1">
              <span className="text-[9px] font-bold text-slate-400">5G</span>
              <Signal className="w-3 h-3 text-slate-200" />
              <Wifi className="w-3 h-3 text-slate-200" />
              <Battery className="w-3.5 h-3.5 text-slate-200 fill-slate-200" />
            </div>
          </div>

          {/* Android WebView Progress Bar (animated when page loads) */}
          {isLoading && (
            <div className="absolute top-7 left-0 right-0 h-[2.5px] bg-slate-800 z-30 overflow-hidden">
              <div className="h-full bg-indigo-500 animate-pulse w-full"></div>
            </div>
          )}

          {/* Full Screen Edge-to-Edge Native WebView Display */}
          <div className="flex-1 w-full bg-white relative overflow-hidden">
            <iframe
              key={iframeKey}
              src={formattedUrl}
              title="Android Native App Screen"
              className="w-full h-full border-0 bg-white"
              sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
              onLoad={() => setIsLoading(false)}
            />
          </div>

          {/* Android Bottom Gesture Navigation Pill */}
          <div className="h-4 bg-black flex items-center justify-center z-30 pointer-events-none">
            <div className="w-24 h-1 bg-white/70 rounded-full"></div>
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
