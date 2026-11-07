'use client';

import React from 'react';
import { 
  Zap, 
  ShieldCheck, 
  Key, 
  Smartphone, 
  RefreshCw, 
  Cpu, 
  DownloadCloud, 
  Lock 
} from 'lucide-react';

const features = [
  {
    icon: <ShieldCheck className="w-6 h-6 text-emerald-600" />,
    title: 'Play Protect Compliant',
    desc: 'Pre-hardened WebView settings with isolated intents and zero dangerous permissions to pass Google Play Protect scans.'
  },
  {
    icon: <Key className="w-6 h-6 text-indigo-600" />,
    title: 'Automated Unique Keystores',
    desc: 'Each build generates a cryptographically secure 2048-bit RSA private keystore with SHA-256 fingerprints.'
  },
  {
    icon: <Smartphone className="w-6 h-6 text-violet-600" />,
    title: 'Both APK & AAB Outputs',
    desc: 'Build ready-to-test release APKs for direct sideloading and optimized App Bundles (AAB) for Google Play publishing.'
  },
  {
    icon: <Cpu className="w-6 h-6 text-amber-600" />,
    title: 'Real-Time Worker Engine',
    desc: 'Separate asynchronous background worker with Redis and SQLite WAL queues, atomic claims, and auto-crash recovery.'
  },
  {
    icon: <RefreshCw className="w-6 h-6 text-cyan-600" />,
    title: 'Native App Experience',
    desc: 'Includes splash screen, pull-to-refresh, hardware back button navigation, and customizable offline retry UI.'
  },
  {
    icon: <Lock className="w-6 h-6 text-rose-600" />,
    title: 'SSRF & DDoS Protection',
    desc: 'Strict DNS inspection blocking private IP ranges, sliding-window rate limiting, and zero third-party telemetry.'
  }
];

export default function Features() {
  return (
    <section id="features" className="py-20 bg-slate-50 border-t border-slate-200/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs font-bold uppercase tracking-widest text-indigo-600 mb-2">
            Why Choose WebToNative
          </h2>
          <h3 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
            Built for High-Throughput & Native Performance
          </h3>
          <p className="mt-4 text-base text-slate-600">
            Everything you need to turn responsive web applications into production-grade Android apps.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((item, idx) => (
            <div 
              key={idx}
              className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="w-12 h-12 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center mb-4">
                {item.icon}
              </div>
              <h4 className="text-lg font-bold text-slate-900 mb-2">
                {item.title}
              </h4>
              <p className="text-sm text-slate-600 leading-relaxed">
                {item.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

