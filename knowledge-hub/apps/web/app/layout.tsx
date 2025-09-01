import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Knowledge Hub',
  description: 'Your intelligent knowledge management system powered by AI',
  keywords: 'knowledge management, AI, documentation, search',
  authors: [{ name: 'Knowledge Hub Team' }],
  creator: 'Knowledge Hub',
  publisher: 'Knowledge Hub',
  robots: 'index, follow',
  viewport: 'width=device-width, initial-scale=1',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <main>{children}</main>
      </body>
    </html>
  )
}
