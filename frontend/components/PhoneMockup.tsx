'use client';

import React from 'react';
import { Wifi, Battery, Signal, Globe, Shield, RefreshCw } from 'lucide-react';

interface PhoneMockupProps {
  appName: string;
  websiteUrl: string;
  iconPreviewUrl: string | null;
}

export default function PhoneMockup({ appName, websiteUrl, iconPreviewUrl }: PhoneMockupProps) {
  const displayAppName = appName.trim() || 'My Web App';
  const displayUrl = websiteUrl.trim() || 'https://yourwebsite.com';

  return (
    <div className="relative mx-auto w-full max-w-[320px] aspect-[9/19] bg-slate-950 rounded-[44px] p-3 shadow-2xl shadow-indigo-950/25 ring-1 ring-slate-800/80">
      {/* Outer Phone Bezel Details */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-5 bg-slate-950 rounded-b-2xl z-30 flex items-center justify-center space-x-2">
        <div className="w-3 h-3 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center">
          <div className="w-1 h-1 rounded-full bg-indigo-950"></div>
        </div>
        <div className="w-10 h-1 bg-slate-800 rounded-full"></div>
      </div>

      {/* Screen Frame */}
      <div className="relative w-full h-full bg-white rounded-[36px] overflow-hidden flex flex-col border border-slate-200">
        {/* Status Bar */}
        <div className="h-7 bg-slate-900 text-white px-5 flex items-center justify-between text-[11px] font-medium tracking-tight select-none z-20">
          <span>9:41</span>
          <div className="flex items-center space-x-1.5">
            <Signal className="w-3 h-3 text-slate-300" />
            <Wifi className="w-3 h-3 text-slate-300" />
            <Battery className="w-3.5 h-3.5 text-slate-300" />
          </div>
        </div>

        {/* In-App Native App Bar */}
        <div className="bg-slate-900 text-white px-3.5 py-2.5 flex items-center justify-between shadow-md z-10 border-b border-slate-800">
          <div className="flex items-center space-x-2.5 min-w-0">
            <div className="w-7 h-7 rounded-lg overflow-hidden bg-slate-800 flex-shrink-0 flex items-center justify-center border border-slate-700">
              {iconPreviewUrl ? (
                <img src={iconPreviewUrl} alt="App Icon" className="w-full h-full object-cover" />
              ) : (
                <Globe className="w-4 h-4 text-indigo-400" />
              )}
            </div>
            <span className="text-xs font-semibold truncate tracking-tight text-slate-100">
              {displayAppName}
            </span>
          </div>
          <div className="flex items-center space-x-1.5 text-slate-400">
            <RefreshCw className="w-3.5 h-3.5" />
          </div>
        </div>

        {/* WebView Screen Content */}
        <div className="flex-1 bg-slate-50 flex flex-col justify-between overflow-hidden relative">
          {/* Simulated Browser Web View */}
          <div className="p-4 flex flex-col items-center justify-center flex-1 text-center">
            <div className="w-14 h-14 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mb-3 shadow-sm">
              {iconPreviewUrl ? (
                <img src={iconPreviewUrl} alt="App Icon" className="w-full h-full object-cover rounded-2xl" />
              ) : (
                <Globe className="w-7 h-7 text-indigo-600" />
              )}
            </div>
            <h4 className="text-sm font-bold text-slate-800 truncate max-w-[200px]">
              {displayAppName}
            </h4>
            <p className="text-[11px] text-slate-500 font-mono mt-0.5 truncate max-w-[220px]">
              {displayUrl}
            </p>

            <div className="mt-4 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-[10px] font-semibold flex items-center space-x-1">
              <Shield className="w-3 h-3 text-emerald-600" />
              <span>Native WebView 2.0 Active</span>
            </div>

            {/* Skeleton mockup lines */}
            <div className="w-full mt-6 space-y-2 px-2">
              <div className="h-16 w-full bg-slate-200/70 rounded-xl animate-pulse"></div>
              <div className="grid grid-cols-2 gap-2">
                <div className="h-12 bg-slate-200/50 rounded-lg"></div>
                <div className="h-12 bg-slate-200/50 rounded-lg"></div>
              </div>
            </div>
          </div>

          {/* Android Bottom Home Bar */}
          <div className="h-5 bg-white flex items-center justify-center border-t border-slate-100">
            <div className="w-24 h-1 bg-slate-300 rounded-full"></div>
          </div>
        </div>
      </div>
    </div>
  );
}

