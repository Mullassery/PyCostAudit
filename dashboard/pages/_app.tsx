import '../styles/globals.css'
import type { AppProps } from 'next/app'
import { useRouter } from 'next/router'
import { useEffect, useState } from 'react'

function MyApp({ Component, pageProps }: AppProps) {
  const router = useRouter()
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      setIsAuthenticated(true)
    } else if (router.pathname !== '/login' && router.pathname !== '/register') {
      router.push('/login')
    }
    setLoading(false)
  }, [router])

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>
  }

  if (!isAuthenticated && router.pathname !== '/login' && router.pathname !== '/register') {
    return null
  }

  return <Component {...pageProps} />
}

export default MyApp
