'use client'

import { useState } from 'react'

// Mock data for demo
const mockAmmoData = [
  {
    id: 1,
    name: '9mm Luger 115gr FMJ',
    brand: 'Federal',
    caliber: '9mm',
    grainWeight: 115,
    bulletType: 'FMJ',
    quantity: 50,
    price: 24.99,
    pricePerRound: 0.50,
    retailer: 'AmmoMart',
    inStock: true,
    image: 'https://via.placeholder.com/100x60/4f46e5/ffffff?text=9mm'
  },
  {
    id: 2,
    name: '.223 Remington 55gr FMJ',
    brand: 'Winchester',
    caliber: '.223',
    grainWeight: 55,
    bulletType: 'FMJ',
    quantity: 20,
    price: 18.99,
    pricePerRound: 0.95,
    retailer: 'BulkAmmo',
    inStock: true,
    image: 'https://via.placeholder.com/100x60/dc2626/ffffff?text=.223'
  },
  {
    id: 3,
    name: '.45 ACP 230gr FMJ',
    brand: 'Remington',
    caliber: '.45 ACP',
    grainWeight: 230,
    bulletType: 'FMJ',
    quantity: 50,
    price: 42.99,
    pricePerRound: 0.86,
    retailer: 'AmmoSeek',
    inStock: false,
    image: 'https://via.placeholder.com/100x60/059669/ffffff?text=.45'
  },
  {
    id: 4,
    name: '5.56x45mm 62gr FMJ',
    brand: 'PMC',
    caliber: '5.56x45',
    grainWeight: 62,
    bulletType: 'FMJ',
    quantity: 30,
    price: 28.99,
    pricePerRound: 0.97,
    retailer: 'Sportsman\'s Guide',
    inStock: true,
    image: 'https://via.placeholder.com/100x60/7c3aed/ffffff?text=5.56'
  },
  {
    id: 5,
    name: '.308 Winchester 150gr SP',
    brand: 'Hornady',
    caliber: '.308',
    grainWeight: 150,
    bulletType: 'SP',
    quantity: 20,
    price: 35.99,
    pricePerRound: 1.80,
    retailer: 'Cabela\'s',
    inStock: true,
    image: 'https://via.placeholder.com/100x60/ea580c/ffffff?text=.308'
  }
]

export default function Home() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCaliber, setSelectedCaliber] = useState('all')
  const [sortBy, setSortBy] = useState('price')

  const calibers = ['all', '9mm', '.223', '.45 ACP', '5.56x45', '.308']

  const filteredAmmo = mockAmmoData
    .filter(ammo => 
      (selectedCaliber === 'all' || ammo.caliber === selectedCaliber) &&
      (searchTerm === '' || ammo.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
       ammo.brand.toLowerCase().includes(searchTerm.toLowerCase()))
    )
    .sort((a, b) => {
      if (sortBy === 'price') return a.pricePerRound - b.pricePerRound
      if (sortBy === 'name') return a.name.localeCompare(b.name)
      return 0
    })

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">
                🎯 Cheapest Ammo Online
              </h1>
            </div>
            <nav className="hidden md:flex space-x-8">
              <a href="#" className="text-gray-700 hover:text-gray-900 font-medium">Home</a>
              <a href="#" className="text-gray-700 hover:text-gray-900 font-medium">Deals</a>
              <a href="#" className="text-gray-700 hover:text-gray-900 font-medium">Retailers</a>
              <a href="#" className="text-gray-700 hover:text-gray-900 font-medium">About</a>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-gradient-to-r from-blue-600 to-purple-600 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl font-bold mb-4">
            Find the Best Ammo Deals Online
          </h2>
          <p className="text-xl mb-8 opacity-90">
            Compare prices from top ammunition retailers and save money on your next purchase
          </p>
          <div className="max-w-2xl mx-auto">
            <div className="flex flex-col sm:flex-row gap-4">
              <input
                type="text"
                placeholder="Search for ammunition..."
                className="flex-1 px-4 py-3 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-white"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              <button className="bg-red-500 hover:bg-red-600 px-8 py-3 rounded-lg font-semibold transition-colors">
                Search Deals
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Filters */}
      <section className="bg-white py-6 border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
            <div className="flex items-center gap-4">
              <label className="font-medium text-gray-700">Caliber:</label>
              <select
                className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={selectedCaliber}
                onChange={(e) => setSelectedCaliber(e.target.value)}
              >
                {calibers.map(caliber => (
                  <option key={caliber} value={caliber}>
                    {caliber === 'all' ? 'All Calibers' : caliber}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-4">
              <label className="font-medium text-gray-700">Sort by:</label>
              <select
                className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
              >
                <option value="price">Price per Round</option>
                <option value="name">Name</option>
              </select>
            </div>
          </div>
        </div>
      </section>

      {/* Results */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h3 className="text-2xl font-bold text-gray-900 mb-2">
            Ammunition Deals ({filteredAmmo.length} results)
          </h3>
          <p className="text-gray-600">
            Showing the best prices from verified retailers
          </p>
        </div>

        <div className="grid gap-4">
          {filteredAmmo.map(ammo => (
            <div key={ammo.id} className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <img
                    src={ammo.image}
                    alt={ammo.name}
                    className="w-20 h-12 object-cover rounded"
                  />
                  <div>
                    <h4 className="font-semibold text-lg text-gray-900">{ammo.name}</h4>
                    <p className="text-gray-600">
                      {ammo.brand} • {ammo.grainWeight}gr {ammo.bulletType} • {ammo.quantity} rounds
                    </p>
                    <p className="text-sm text-gray-500">Sold by {ammo.retailer}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-green-600">
                    ${ammo.price}
                  </div>
                  <div className="text-sm text-gray-600">
                    ${ammo.pricePerRound.toFixed(3)}/round
                  </div>
                  <div className="mt-2">
                    {ammo.inStock ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        In Stock
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        Out of Stock
                      </span>
                    )}
                  </div>
                  <button 
                    className={`mt-3 px-6 py-2 rounded-lg font-medium transition-colors ${
                      ammo.inStock 
                        ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                        : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    }`}
                    disabled={!ammo.inStock}
                  >
                    {ammo.inStock ? 'View Deal' : 'Notify Me'}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-12 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <h5 className="font-bold text-lg mb-4">Cheapest Ammo Online</h5>
              <p className="text-gray-300">
                Your trusted source for finding the best ammunition deals online.
              </p>
            </div>
            <div>
              <h6 className="font-semibold mb-4">Popular Calibers</h6>
              <ul className="space-y-2 text-gray-300">
                <li><a href="#" className="hover:text-white">9mm Luger</a></li>
                <li><a href="#" className="hover:text-white">.223 Remington</a></li>
                <li><a href="#" className="hover:text-white">.45 ACP</a></li>
                <li><a href="#" className="hover:text-white">5.56x45mm</a></li>
              </ul>
            </div>
            <div>
              <h6 className="font-semibold mb-4">Resources</h6>
              <ul className="space-y-2 text-gray-300">
                <li><a href="#" className="hover:text-white">Price Alerts</a></li>
                <li><a href="#" className="hover:text-white">Retailer Reviews</a></li>
                <li><a href="#" className="hover:text-white">Ammo Guide</a></li>
                <li><a href="#" className="hover:text-white">Contact</a></li>
              </ul>
            </div>
            <div>
              <h6 className="font-semibold mb-4">Legal</h6>
              <ul className="space-y-2 text-gray-300">
                <li><a href="#" className="hover:text-white">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-white">Terms of Service</a></li>
                <li><a href="#" className="hover:text-white">Disclaimer</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-700 mt-8 pt-8 text-center text-gray-300">
            <p>&copy; 2024 Cheapest Ammo Online. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
} 