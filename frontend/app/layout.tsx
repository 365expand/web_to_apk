import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'WebToNative | Convert Any Website into a Native Android App',
  description: 'Turn your website or web app into a high-performance, signed Android APK and AAB in minutes. Production-ready with automated keystores and zero coding required.',
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className="antialiased selection:bg-indigo-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}

