import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'

export default function Layout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [menuOpen, setMenuOpen] = useState(false)

  const logout = () => {
    localStorage.removeItem('token')
    router.push('/login')
  }

  const isActive = (path: string) => router.pathname === path

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className="w-64 bg-gray-900 text-white">
        <div className="p-6">
          <h1 className="text-2xl font-bold">PyCostAudit</h1>
          <p className="text-gray-400 text-sm">Cost Dashboard</p>
        </div>

        <nav className="mt-6">
          <Link href="/">
            <a className={`block px-6 py-3 ${isActive('/') ? 'bg-blue-600' : 'hover:bg-gray-800'}`}>
              📊 Overview
            </a>
          </Link>
          <Link href="/breakdown">
            <a className={`block px-6 py-3 ${isActive('/breakdown') ? 'bg-blue-600' : 'hover:bg-gray-800'}`}>
              📈 Breakdown
            </a>
          </Link>
          <Link href="/budget">
            <a className={`block px-6 py-3 ${isActive('/budget') ? 'bg-blue-600' : 'hover:bg-gray-800'}`}>
              💰 Budget
            </a>
          </Link>
          <Link href="/alerts">
            <a className={`block px-6 py-3 ${isActive('/alerts') ? 'bg-blue-600' : 'hover:bg-gray-800'}`}>
              🔔 Alerts
            </a>
          </Link>
          <Link href="/settings">
            <a className={`block px-6 py-3 ${isActive('/settings') ? 'bg-blue-600' : 'hover:bg-gray-800'}`}>
              ⚙️ Settings
            </a>
          </Link>
        </nav>

        <div className="absolute bottom-6 left-6 right-6">
          <button
            onClick={logout}
            className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 rounded text-sm"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <header className="bg-white shadow">
          <div className="px-6 py-4 flex justify-between items-center">
            <h2 className="text-xl font-bold text-gray-900">
              {router.pathname === '/' && 'Dashboard'}
              {router.pathname === '/breakdown' && 'Cost Breakdown'}
              {router.pathname === '/budget' && 'Budget Settings'}
              {router.pathname === '/alerts' && 'Alerts'}
              {router.pathname === '/settings' && 'Settings'}
            </h2>
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="text-gray-600 hover:text-gray-900"
            >
              👤 Account
            </button>
          </div>
        </header>

        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
