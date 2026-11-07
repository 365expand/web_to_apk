'use client';

import React, { useState, useEffect } from 'react';
import { Wifi, Battery, Signal, Globe, Shield, RefreshCw, ExternalLink, Smartphone, Sparkles } from 'lucide-react';

interface PhoneMockupProps {
  appName: string;
  websiteUrl: string;
  iconPreviewUrl: string | null;
}

export default function PhoneMockup({ appName, websiteUrl, iconPreviewUrl }: PhoneMockupProps) {
  const displayAppName = appName.trim() || 'My Web App';
  
  // Format URL nicely for iframe
  const rawUrl = websiteUrl.trim();
  const formattedUrl = rawUrl
    ? (rawUrl.startsWith('http://') || rawUrl.startsWith('https://') ? rawUrl : `https://${rawUrl}`)
    : 'https://example.com';

  const [previewMode, setPreviewMode] = useState<'live' | 'brand'>('live');
  const [iframeKey, setIframeKey] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  // When url changes, reload iframe and show loading
  useEffect(() => {
    setIsLoading(true);
    setIframeKey(k => k + 1);
  }, [formattedUrl]);

  return (
    <div className="flex flex-col items-center w-full max-w-[340px] mx-auto">
      {/* Mode Switcher Buttons */}
      <div className="flex items-center space-x-1.5 p-1 bg-slate-900/90 rounded-full border border-slate-800 mb-4 shadow-lg">
        <button
          type="button"
          onClick={() => setPreviewMode('live')}
          className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all ${
            previewMode === 'live'
              ? 'bg-indigo-600 text-white shadow'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Smartphone className="w-3.5 h-3.5" />
          <span>Live Web Preview</span>
        </button>
        <button
          type="button"
          onClick={() => setPreviewMode('brand')}
          className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all ${
            previewMode === 'brand'
              ? 'bg-indigo-600 text-white shadow'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>App Identity</span>
        </button>
      </div>

      {/* Phone Hardware Mockup */}
      <div className="relative w-full aspect-[9/19] bg-slate-950 rounded-[46px] p-3 shadow-2xl shadow-indigo-950/40 ring-1 ring-slate-800">
        {/* Outer Phone Bezel Details / Speaker & Camera Notch */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-5 bg-slate-950 rounded-b-2xl z-30 flex items-center justify-center space-x-2">
          <div className="w-2.5 h-2.5 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center">
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
          <div className="bg-slate-900 text-white px-3.5 py-2.5 flex items-center justify-between shadow-md z-20 border-b border-slate-800">
            <div className="flex items-center space-x-2.5 min-w-0">
              <div className="w-7 h-7 rounded-lg overflow-hidden bg-slate-800 flex-shrink-0 flex items-center justify-center border border-slate-700">
                {iconPreviewUrl ? (
                  <img src={iconPreviewUrl} alt="App Icon" className="w-full h-full object-cover" />
                ) : (
                  <Globe className="w-4 h-4 text-indigo-400" />
                )}
              </div>
              <div className="truncate">
                <span className="text-xs font-semibold block truncate tracking-tight text-slate-100">
                  {displayAppName}
                </span>
                <span className="text-[10px] text-slate-400 block truncate font-mono">
                  {rawUrl ? formattedUrl.replace(/^https?:\/\//, '') : 'example.com'}
                </span>
              </div>
            </div>
            <div className="flex items-center space-x-2 text-slate-400">
              <button
                type="button"
                onClick={() => {
                  setIsLoading(true);
                  setIframeKey(k => k + 1);
                }}
                title="Reload Web Page"
                className="hover:text-white transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
              <a
                href={formattedUrl}
                target="_blank"
                rel="noreferrer"
                title="Open in new tab"
                className="hover:text-white transition-colors"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>

          {/* Screen Content */}
          <div className="flex-1 bg-slate-50 relative flex flex-col overflow-hidden">
            {previewMode === 'live' ? (
              <div className="relative w-full h-full">
                {isLoading && (
                  <div className="absolute inset-0 bg-slate-100 flex flex-col items-center justify-center z-10 p-4">
                    <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mb-2"></div>
                    <span className="text-xs text-slate-500 font-medium">Loading preview...</span>
                  </div>
                )}
                <iframe
                  key={iframeKey}
                  src={formattedUrl}
                  title="App Live Preview"
                  className="w-full h-full border-0"
                  sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
                  onLoad={() => setIsLoading(false)}
                />
              </div>
            ) : (
              /* Simulated Splash / App Identity View */
              <div className="p-4 flex flex-col items-center justify-center flex-1 text-center bg-gradient-to-b from-white to-slate-50">
                <div className="w-16 h-16 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mb-3 shadow-md shadow-indigo-100">
                  {iconPreviewUrl ? (
                    <img src={iconPreviewUrl} alt="App Icon" className="w-full h-full object-cover rounded-2xl" />
                  ) : (
                    <Globe className="w-8 h-8 text-indigo-600" />
                  )}
                </div>
                <h4 className="text-sm font-bold text-slate-800 truncate max-w-[200px]">
                  {displayAppName}
                </h4>
                <p className="text-[11px] text-slate-500 font-mono mt-0.5 truncate max-w-[220px]">
                  {formattedUrl}
                </p>

                <div className="mt-4 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-[10px] font-semibold flex items-center space-x-1">
                  <Shield className="w-3 h-3 text-emerald-600" />
                  <span>Native WebView Engine v2.0 Active</span>
                </div>

                <div className="w-full mt-6 space-y-2 px-2">
                  <div className="p-3 bg-white rounded-xl border border-slate-100 shadow-sm text-left">
                    <div className="text-[11px] font-medium text-slate-700">Internal Page Navigation</div>
                    <div className="text-[10px] text-slate-400">All links, subdomains & session cookies remain inside the app.</div>
                  </div>
                  <div className="p-3 bg-white rounded-xl border border-slate-100 shadow-sm text-left">
                    <div className="text-[11px] font-medium text-slate-700">Offline & Hardware Features</div>
                    <div className="text-[10px] text-slate-400">File uploads, camera, geolocation & full screen.</div>
                  </div>
                </div>
              </div>
            )}

            {/* Android Bottom Navigation Bar */}
            <div className="h-6 bg-white flex items-center justify-center border-t border-slate-100 z-10">
              <div className="w-24 h-1 bg-slate-300 rounded-full"></div>
            </div>
          </div>
        </div>
      </div>
      <p className="text-xs text-slate-400 text-center mt-3">
        Interactive preview updates live as you type your URL
      </p>
    </div>
  );
}
