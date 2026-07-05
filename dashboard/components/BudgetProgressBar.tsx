interface BudgetProgressBarProps {
  spent: number
  budget: number
  forecast: number
}

export default function BudgetProgressBar({ spent, budget, forecast }: BudgetProgressBarProps) {
  const percent = (spent / budget) * 100
  const forecastPercent = (forecast / budget) * 100

  let color = 'bg-green-500'
  if (percent > 90) color = 'bg-red-500'
  else if (percent > 75) color = 'bg-yellow-500'
  else if (percent > 50) color = 'bg-blue-500'

  return (
    <div>
      <div className="flex justify-between text-sm mb-2">
        <span>Budget Usage</span>
        <span>{percent.toFixed(1)}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-4">
        <div
          className={`${color} h-4 rounded-full transition-all duration-300`}
          style={{ width: `${Math.min(percent, 100)}%` }}
        />
      </div>
      <div className="mt-2 flex justify-between text-xs text-gray-600">
        <span>${spent.toFixed(2)} spent</span>
        <span>${budget.toFixed(2)} budget</span>
        <span>${forecast.toFixed(2)} forecast</span>
      </div>
    </div>
  )
}
