interface ProviderBreakdownChartProps {
  data: Record<string, number>
}

export default function ProviderBreakdownChart({ data }: ProviderBreakdownChartProps) {
  const total = Object.values(data).reduce((a, b) => a + b, 0)
  const colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b']

  return (
    <div className="flex gap-6">
      {/* Pie chart representation */}
      <div className="w-40 h-40 rounded-full border-8 border-blue-500 flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-bold">${total.toFixed(2)}</div>
          <div className="text-xs text-gray-600">Total</div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex-1">
        {Object.entries(data).map(([provider, cost], i) => (
          <div key={provider} className="mb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: colors[i % colors.length] }}
                />
                <span className="text-sm font-medium capitalize">{provider}</span>
              </div>
              <span className="text-sm font-bold">${cost.toFixed(2)}</span>
            </div>
            <div className="text-xs text-gray-600">
              {((cost / total) * 100).toFixed(1)}%
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
