export default function CostTrendChart() {
  return (
    <div className="h-64 flex items-end justify-between gap-2">
      {/* Placeholder bars for demo */}
      {[12, 18, 15, 22, 19, 25, 20].map((height, i) => (
        <div
          key={i}
          className="flex-1 bg-blue-500 rounded-t hover:bg-blue-600"
          style={{ height: `${height}%` }}
        >
          <div className="text-xs text-center text-gray-600 mt-1">Day {i + 1}</div>
        </div>
      ))}
    </div>
  )
}
