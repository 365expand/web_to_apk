'use client';

import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import AppBuilder from '../components/AppBuilder';
import PhoneMockup from '../components/PhoneMockup';
import Features from '../components/Features';
import Footer from '../components/Footer';
import { Sparkles, ShieldCheck, CheckCircle2, ArrowRight } from 'lucide-react';

export default function Home() {
  const [appName, setAppName] = useState('365expand');
  const [websiteUrl, setWebsiteUrl] = useState('https://365expand.com/');
  const [iconPreviewUrl, setIconPreviewUrl] = useState<string | null>(null);

  return (
    <main className="min-h-screen flex flex-col bg-slate-50/50">
      <Navbar />

      {/* Hero & Interactive Builder Section */}
      <section id="builder" className="relative pt-12 pb-20 overflow-hidden">
        {/* Subtle background glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-96 bg-gradient-to-b from-indigo-100/50 via-violet-50/20 to-transparent pointer-events-none -z-10 blur-3xl" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header Title */}
          <div className="text-center max-w-3xl mx-auto mb-12">
            <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-indigo-50 border border-indigo-200/80 text-indigo-700 text-xs font-semibold mb-4 shadow-sm">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Convert Website to Android APK & AAB</span>
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-slate-900 tracking-tight leading-[1.15]">
              Turn your website into a <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-800">Native Android App</span> in minutes.
            </h1>
            <p className="mt-5 text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
              No coding, no subscription, and no cloud dependencies. Fast, rate-limited, and signed with your own automated keystore.
            </p>

            <div className="mt-6 flex flex-wrap items-center justify-center gap-4 text-xs font-medium text-slate-600">
              <span className="flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                <span>Signed APK + AAB</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                <span>Play Protect Hardened</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                <span>Redis & Worker Queue</span>
              </span>
            </div>
          </div>

          {/* Dual Column Studio Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left Column: Interactive App Builder */}
            <div className="lg:col-span-7">
              <AppBuilder 
                appName={appName}
                setAppName={setAppName}
                websiteUrl={websiteUrl}
                setWebsiteUrl={setWebsiteUrl}
                iconPreviewUrl={iconPreviewUrl}
                setIconPreviewUrl={setIconPreviewUrl}
              />
            </div>

            {/* Right Column: Live Interactive Phone Mockup */}
            <div className="lg:col-span-5 sticky top-24 flex flex-col items-center">
              <div className="w-full text-center mb-3">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 flex items-center justify-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-indigo-500 animate-ping"></span>
                  <span>Live App Preview</span>
                </span>
              </div>
              <PhoneMockup 
                appName={appName}
                websiteUrl={websiteUrl}
                iconPreviewUrl={iconPreviewUrl}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <Features />

      {/* How it works simple 3-step section */}
      <section id="how-it-works" className="py-20 bg-white border-t border-slate-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-xs font-bold uppercase tracking-widest text-indigo-600 mb-2">Workflow</h2>
            <h3 className="text-3xl font-extrabold text-slate-900 tracking-tight">How It Works in 3 Simple Steps</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200/80 relative">
              <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white font-bold flex items-center justify-center text-sm mb-4">
                01
              </div>
              <h4 className="text-base font-bold text-slate-900 mb-2">Provide Website URL & Icon</h4>
              <p className="text-xs text-slate-600 leading-relaxed">
                Enter your live website URL and brand logo. The system automatically derives safe package IDs and generates high-res adaptive mipmaps.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200/80 relative">
              <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white font-bold flex items-center justify-center text-sm mb-4">
                02
              </div>
              <h4 className="text-base font-bold text-slate-900 mb-2">Asynchronous Worker Build</h4>
              <p className="text-xs text-slate-600 leading-relaxed">
                An isolated background worker builds both APK and AAB with Gradle, creates an RSA-2048 signing keystore, and verifies signatures.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200/80 relative">
              <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white font-bold flex items-center justify-center text-sm mb-4">
                03
              </div>
              <h4 className="text-base font-bold text-slate-900 mb-2">Download & Publish</h4>
              <p className="text-xs text-slate-600 leading-relaxed">
                Download the release APK for immediate testing on your Android phone, or upload the AAB directly to Google Play Console.
              </p>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}

