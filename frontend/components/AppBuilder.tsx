'use client';

import React, { useState, useEffect, useRef } from 'react';
import { 
  Globe, 
  Sparkles, 
  Upload, 
  Settings2, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  Download, 
  KeyRound, 
  Box, 
  Archive,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  ExternalLink
} from 'lucide-react';

interface AppBuilderProps {
  appName: string;
  setAppName: (name: string) => void;
  websiteUrl: string;
  setWebsiteUrl: (url: string) => void;
  iconPreviewUrl: string | null;
  setIconPreviewUrl: (url: string | null) => void;
}

interface BuildState {
  id: string;
  status: 'idle' | 'queued' | 'processing' | 'completed' | 'failed';
  step: string;
  progress: number;
  error?: string;
  packageName?: string;
  queuePosition?: number;
  etaSeconds?: number;
}

export default function AppBuilder({
  appName,
  setAppName,
  websiteUrl,
  setWebsiteUrl,
  iconPreviewUrl,
  setIconPreviewUrl
}: AppBuilderProps) {
  const [iconFile, setIconFile] = useState<File | null>(null);
  const [packageName, setPackageName] = useState('');
  const [autoPackage, setAutoPackage] = useState('com.webtoapk.app');
  const [versionCode, setVersionCode] = useState(1);
  const [versionName, setVersionName] = useState('1.0.0');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [buildState, setBuildState] = useState<BuildState | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Derive package name from website URL
  useEffect(() => {
    if (!websiteUrl) {
      setAutoPackage('com.webtoapk.app');
      return;
    }
    try {
      let clean = websiteUrl.trim();
      if (!clean.startsWith('http://') && !clean.startsWith('https://')) {
        clean = 'https://' + clean;
      }
      const parsed = new URL(clean);
      let host = parsed.hostname.toLowerCase();
      if (host.startsWith('www.')) host = host.slice(4);

      let parts = host.split('.').filter(Boolean);
      if (parts.length > 0) parts.pop(); // remove TLD
      parts.reverse();

      let sanitized = parts.map(part => {
        let cleanPart = part.replace(/[^a-z0-9_]/g, '');
        if (/^[0-9]/.test(cleanPart)) cleanPart = 'p' + cleanPart;
        return cleanPart;
      }).filter(Boolean);

      let pkg = 'com.' + (sanitized.join('.') || 'app') + '.app';
      setAutoPackage(pkg);
    } catch {
      setAutoPackage('com.webtoapk.app');
    }
  }, [websiteUrl]);

  // Handle icon selection
  const handleIconChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setErrorMsg('Please upload a valid image file (PNG, JPG, or WEBP).');
      return;
    }

    const img = new Image();
    const objectUrl = URL.createObjectURL(file);
    img.onload = () => {
      const ratio = img.width / img.height;
      if (ratio < 0.85 || ratio > 1.15) {
        setErrorMsg('Icon must be 1:1 square aspect ratio (e.g., 512x512).');
        URL.revokeObjectURL(objectUrl);
        return;
      }
      setErrorMsg(null);
      setIconFile(file);
      setIconPreviewUrl(objectUrl);
    };
    img.src = objectUrl;
  };

  // Submit build request
  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    let cleanUrl = websiteUrl.trim();
    if (!cleanUrl) {
      setErrorMsg('Please provide a valid Website URL.');
      return;
    }
    if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
      cleanUrl = 'https://' + cleanUrl;
      setWebsiteUrl(cleanUrl);
    }

    if (!appName.trim()) {
      setErrorMsg('Please provide an App Name.');
      return;
    }

    if (!iconFile) {
      setErrorMsg('Please upload a 1:1 square App Icon.');
      return;
    }

    setIsSubmitting(true);

    try {
      const formData = new FormData();
      formData.append('website_url', cleanUrl);
      formData.append('app_name', appName.trim());
      formData.append('icon', iconFile);
      if (packageName.trim()) {
        formData.append('package_name', packageName.trim());
      }
      formData.append('version_code', versionCode.toString());
      formData.append('version_name', versionName.trim() || '1.0.0');

      const res = await fetch('/api/v1/builds', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to initialize build request.');
      }

      setBuildState({
        id: data.id,
        status: data.status,
        step: data.step || 'validating',
        progress: data.progress || 10,
        packageName: data.package_name,
        queuePosition: data.queue_position,
        etaSeconds: data.eta_seconds,
      });
    } catch (err: any) {
      setErrorMsg(err.message || 'Network error communicating with build API.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Poll build status
  useEffect(() => {
    if (!buildState?.id || buildState.status === 'completed' || buildState.status === 'failed') {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/v1/builds/${buildState.id}`);
        if (!res.ok) return;
        const data = await res.json();

        setBuildState(prev => {
          if (!prev) return null;
          return {
            ...prev,
            status: data.status,
            step: data.step,
            progress: data.progress,
            error: data.error,
            queuePosition: data.queue_position,
            etaSeconds: data.eta_seconds,
          };
        });
      } catch (e) {
        // Retry silently on intermittent poll failure
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [buildState?.id, buildState?.status]);

  return (
    <div className="bg-white rounded-3xl border border-slate-200/90 shadow-xl shadow-slate-200/50 p-6 sm:p-8">
      <div className="mb-6">
        <h3 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center space-x-2">
          <span>App Configuration</span>
          <span className="text-indigo-600">⚡</span>
        </h3>
        <p className="text-sm text-slate-500 mt-1">
          Enter your website details and brand icon to compile your native Android bundle.
        </p>
      </div>

      {errorMsg && (
        <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-600" />
          <div className="flex-1">{errorMsg}</div>
        </div>
      )}

      {/* Build Progress Card (Shows when job is active) */}
      {buildState && (
        <div className="mb-8 p-6 rounded-2xl bg-slate-900 text-white border border-slate-800 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-mono uppercase px-2.5 py-1 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Build ID: {buildState.id.slice(0, 10)}...
              </span>
              <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                buildState.status === 'completed'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : buildState.status === 'failed'
                  ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                  : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center space-x-1.5'
              }`}>
                {buildState.status === 'processing' && <Loader2 className="w-3 h-3 animate-spin" />}
                <span className="capitalize">{buildState.status}</span>
              </span>
            </div>
            <span className="text-sm font-bold font-mono text-indigo-400">
              {buildState.progress}%
            </span>
          </div>

          {/* Progress Bar */}
          <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden mb-3">
            <div
              className={`h-full transition-all duration-500 ease-out ${
                buildState.status === 'completed'
                  ? 'bg-emerald-500'
                  : buildState.status === 'failed'
                  ? 'bg-rose-500'
                  : 'bg-gradient-to-r from-indigo-500 to-violet-500'
              }`}
              style={{ width: `${buildState.progress}%` }}
            ></div>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-400 mb-4">
            <span className="capitalize flex items-center space-x-1">
              <span>Step:</span>
              <strong className="text-slate-200 font-mono">{buildState.step}</strong>
            </span>
            {buildState.queuePosition !== undefined && buildState.queuePosition > 0 && (
              <span>Queue position: #{buildState.queuePosition}</span>
            )}
          </div>

          {/* Failure Message */}
          {buildState.status === 'failed' && (
            <div className="p-3.5 rounded-xl bg-rose-950/60 border border-rose-800/80 text-rose-300 text-xs mt-3">
              <strong className="block font-semibold mb-1">Build Failed:</strong>
              {buildState.error || 'Unknown error occurred during Gradle compilation.'}
            </div>
          )}

          {/* Success Download Actions */}
          {buildState.status === 'completed' && (
            <div className="pt-4 border-t border-slate-800 space-y-3">
              <div className="text-xs font-semibold text-emerald-400 flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Build Successful! All outputs signed and verified.</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                <a
                  href={`/api/v1/builds/${buildState.id}/download/apk`}
                  download
                  className="flex items-center justify-center space-x-2 px-3.5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition-all active:scale-95 shadow-sm"
                >
                  <Download className="w-4 h-4" />
                  <span>Download APK</span>
                </a>
                <a
                  href={`/api/v1/builds/${buildState.id}/download/aab`}
                  download
                  className="flex items-center justify-center space-x-2 px-3.5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-all active:scale-95 shadow-sm"
                >
                  <Box className="w-4 h-4" />
                  <span>Download AAB</span>
                </a>
                <a
                  href={`/api/v1/builds/${buildState.id}/download/bundle`}
                  download
                  className="flex items-center justify-center space-x-2 px-3.5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold text-xs transition-all active:scale-95"
                >
                  <Archive className="w-4 h-4" />
                  <span>Full Bundle</span>
                </a>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Main Configuration Form */}
      <form onSubmit={handleGenerate} className="space-y-5">
        {/* Website URL */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
            Website URL <span className="text-rose-500">*</span>
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <Globe className="w-4 h-4" />
            </div>
            <input
              type="text"
              value={websiteUrl}
              onChange={(e) => setWebsiteUrl(e.target.value)}
              placeholder="https://example.com"
              required
              className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-600 focus:border-indigo-600 transition-all font-mono"
            />
          </div>
          <span className="text-[11px] text-slate-400 mt-1 block">
            Auto-validated: Only public HTTP/HTTPS URLs allowed (SSRF shielded).
          </span>
        </div>

        {/* App Name */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
            App Name <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            value={appName}
            onChange={(e) => setAppName(e.target.value)}
            placeholder="My Mobile App"
            maxLength={100}
            required
            className="w-full px-4 py-3 rounded-xl border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-600 focus:border-indigo-600 transition-all"
          />
        </div>

        {/* 1:1 App Icon Upload */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
            App Icon (1:1 Square) <span className="text-rose-500">*</span>
          </label>
          <div 
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-slate-300 hover:border-indigo-500 rounded-2xl p-5 text-center cursor-pointer transition-colors bg-slate-50/50 hover:bg-indigo-50/20"
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={handleIconChange}
              className="hidden"
            />
            {iconPreviewUrl ? (
              <div className="flex items-center justify-center space-x-4">
                <img
                  src={iconPreviewUrl}
                  alt="Icon Preview"
                  className="w-16 h-16 rounded-2xl object-cover shadow-md border border-slate-200"
                />
                <div className="text-left">
                  <p className="text-xs font-semibold text-slate-800">
                    {iconFile?.name || 'Icon Selected'}
                  </p>
                  <p className="text-[11px] text-indigo-600 font-medium mt-0.5">
                    Click to change image
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center">
                <div className="w-10 h-10 rounded-full bg-indigo-100/70 text-indigo-600 flex items-center justify-center mb-2">
                  <Upload className="w-5 h-5" />
                </div>
                <p className="text-xs font-semibold text-slate-700">
                  Click to upload or drag & drop icon
                </p>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Square PNG, JPG, or WEBP (min 192x192, 512x512 recommended)
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Advanced Settings Accordion */}
        <div className="border border-slate-200 rounded-2xl overflow-hidden">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="w-full px-4 py-3 bg-slate-50/80 hover:bg-slate-100 flex items-center justify-between text-xs font-semibold text-slate-700 transition-colors"
          >
            <span className="flex items-center space-x-2">
              <Settings2 className="w-4 h-4 text-slate-500" />
              <span>Advanced Android Settings (Optional)</span>
            </span>
            {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showAdvanced && (
            <div className="p-4 space-y-4 bg-white border-t border-slate-200 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1.5">
                  Package Name (Application ID)
                </label>
                <input
                  type="text"
                  value={packageName}
                  onChange={(e) => setPackageName(e.target.value)}
                  placeholder={autoPackage}
                  className="w-full px-3 py-2.5 rounded-lg border border-slate-300 font-mono text-xs focus:ring-2 focus:ring-indigo-600"
                />
                <span className="text-[10px] text-slate-400 mt-1 block">
                  Default: <code className="bg-slate-100 px-1 py-0.5 rounded font-mono">{autoPackage}</code>
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1.5">Version Code</label>
                  <input
                    type="number"
                    min="1"
                    value={versionCode}
                    onChange={(e) => setVersionCode(parseInt(e.target.value) || 1)}
                    className="w-full px-3 py-2.5 rounded-lg border border-slate-300 font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1.5">Version Name</label>
                  <input
                    type="text"
                    value={versionName}
                    onChange={(e) => setVersionName(e.target.value)}
                    placeholder="1.0.0"
                    className="w-full px-3 py-2.5 rounded-lg border border-slate-300 font-mono text-xs"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Generate Button */}
        <button
          type="submit"
          disabled={isSubmitting || buildState?.status === 'processing'}
          className="w-full py-3.5 px-6 rounded-xl font-bold text-sm text-white bg-gradient-to-r from-indigo-600 via-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 active:scale-[0.98] transition-all shadow-lg shadow-indigo-600/30 flex items-center justify-center space-x-2 disabled:opacity-60 disabled:pointer-events-none"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Initializing Build...</span>
            </>
          ) : buildState?.status === 'processing' ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Compiling Android App...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>Generate Android App</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}

