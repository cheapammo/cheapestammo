import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Cheapest Ammo Online - Best Ammo Prices Comparison',
  description: 'Find the cheapest ammo prices online. Compare ammunition deals from top retailers and save money on your next purchase.',
  keywords: 'ammo, ammunition, cheap ammo, ammo prices, gun ammo, bullets',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50">
        {children}
      </body>
    </html>
  )
} 