import { useState, useEffect } from 'react'
import Link from 'next/link'
import Layout from '../components/Layout'
import MetricsCard from '../components/MetricsCard'
import CostTrendChart from '../components/CostTrendChart'
import ProviderBreakdownChart from '../components/ProviderBreakdownChart'
import BudgetProgressBar from '../components/BudgetProgressBar'

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [budget, setBudget] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchData()
  }, [])

  async function fetchData() {
    try {
      const token = localStorage.getItem('token')
      const headers = { Authorization: `Bearer ${token}` }

      // Fetch cost summary
      const summaryRes = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/costs/summary`,
        { headers }
      )
      const summaryData = await summaryRes.json()
      setSummary(summaryData)

      // Fetch budget status
      const budgetRes = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/budget/status`,
        { headers }
      )
      const budgetData = await budgetRes.json()
      setBudget(budgetData)

      setLoading(false)
    } catch (err) {
      console.error('Error fetching data:', err)
      setError('Failed to load dashboard data')
      setLoading(false)
    }
  }

  if (loading) return <Layout><div className="text-center py-10">Loading...</div></Layout>
  if (error) return <Layout><div className="text-red-500 py-10">{error}</div></Layout>

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600">Real-time cost tracking and optimization</p>
          </div>
          <div className="space-x-2">
            <Link href="/breakdown">
              <a className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
                View Breakdown
              </a>
            </Link>
            <Link href="/budget">
              <a className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600">
                Budget Settings
              </a>
            </Link>
          </div>
        </div>

        {/* Metrics Cards */}
        {summary && (
          <div className="grid grid-cols-3 gap-4">
            <MetricsCard
              label="Today"
              value={`$${summary.total_today?.toFixed(2) || '0.00'}`}
              change="+5.2%"
            />
            <MetricsCard
              label="This Week"
              value={`$${summary.total_7d?.toFixed(2) || '0.00'}`}
              change="+12.1%"
            />
            <MetricsCard
              label="This Month"
              value={`$${summary.total_30d?.toFixed(2) || '0.00'}`}
              change="+8.3%"
            />
          </div>
        )}

        {/* Budget Status */}
        {budget && !budget.error && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Budget Status</h2>
            <BudgetProgressBar
              spent={budget.spent}
              budget={budget.budget_amount}
              forecast={budget.forecast_end_amount}
            />
            <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Remaining</p>
                <p className="text-lg font-bold">${budget.remaining?.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-gray-600">Daily Rate</p>
                <p className="text-lg font-bold">${budget.daily_rate?.toFixed(2)}/day</p>
              </div>
              <div>
                <p className="text-gray-600">Projected</p>
                <p className="text-lg font-bold">${budget.forecast_end_amount?.toFixed(2)}</p>
              </div>
            </div>
          </div>
        )}

        {/* Charts */}
        <div className="grid grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Cost Trend</h2>
            <CostTrendChart />
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Provider Breakdown</h2>
            {summary?.by_provider && (
              <ProviderBreakdownChart data={summary.by_provider} />
            )}
          </div>
        </div>

        {/* Summary Stats */}
        {summary && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Summary</h2>
            <div className="grid grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Operations</p>
                <p className="text-2xl font-bold">{summary.num_operations}</p>
              </div>
              <div>
                <p className="text-gray-600">Providers</p>
                <p className="text-2xl font-bold">
                  {Object.keys(summary.by_provider || {}).length}
                </p>
              </div>
              <div>
                <p className="text-gray-600">Models</p>
                <p className="text-2xl font-bold">
                  {Object.keys(summary.by_model || {}).length}
                </p>
              </div>
              <div>
                <p className="text-gray-600">Avg Cost/Op</p>
                <p className="text-2xl font-bold">
                  ${
                    summary.num_operations > 0
                      ? (summary.total_30d / summary.num_operations).toFixed(4)
                      : '0'
                  }
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}
