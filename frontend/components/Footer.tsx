'use client';

import React from 'react';
import { Smartphone, Heart, Shield } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-400 py-12 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white">
            <Smartphone className="w-4 h-4" />
          </div>
          <span className="text-lg font-bold text-white tracking-tight">WebToNative</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">Open Source</span>
        </div>

        <div className="flex items-center space-x-6 text-sm text-slate-400">
          <span className="flex items-center space-x-1.5">
            <Shield className="w-4 h-4 text-emerald-400" />
            <span>Zero Third-Party APIs</span>
          </span>
          <span>•</span>
          <span>FastAPI + Gradle SDK</span>
          <span>•</span>
          <span>Redis & SQLite Queue</span>
        </div>

        <p className="text-xs text-slate-500">
          &copy; {new Date().getFullYear()} WebToNative Studio. All rights reserved.
        </p>
      </div>
    </footer>
  );
}

