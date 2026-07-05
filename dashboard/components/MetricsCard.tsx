interface MetricsCardProps {
  label: string
  value: string
  change: string
  trend?: 'up' | 'down'
}

export default function MetricsCard({ label, value, change, trend = 'up' }: MetricsCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <p className="text-gray-600 text-sm font-medium">{label}</p>
      <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
      <p className={`text-sm mt-2 ${trend === 'up' ? 'text-red-500' : 'text-green-500'}`}>
        {change} from last period
      </p>
    </div>
  )
}
