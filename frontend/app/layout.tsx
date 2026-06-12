import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AI Travel Concierge',
  description: 'Your intelligent travel planning assistant',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
