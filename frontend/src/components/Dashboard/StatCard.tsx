interface StatCardProps {
  title: string
  value: string | number
  icon: string
  change?: number
  changeLabel?: string
  gradient?: 'blue' | 'green' | 'purple' | 'orange'
}

const gradientStyles = {
  blue: 'from-blue-500 to-blue-600',
  green: 'from-green-500 to-green-600',
  purple: 'from-purple-500 to-purple-600',
  orange: 'from-orange-500 to-orange-600',
}

export default function StatCard({
  title,
  value,
  icon,
  change,
  changeLabel,
  gradient = 'blue',
}: StatCardProps) {
  const isPositive = change !== undefined && change >= 0
  
  return (
    <div className={`bg-gradient-to-br ${gradientStyles[gradient]} rounded-xl p-5 text-white shadow-lg`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-3xl opacity-90">{icon}</span>
        {change !== undefined && (
          <div className={`flex items-center gap-1 text-sm font-medium px-2 py-1 rounded-full ${
            isPositive ? 'bg-white/20' : 'bg-white/20'
          }`}>
            <span>{isPositive ? '↑' : '↓'}</span>
            <span>{Math.abs(change)}%</span>
          </div>
        )}
      </div>
      <div className="text-3xl font-bold mb-1">{value}</div>
      <div className="text-sm opacity-80">{title}</div>
      {changeLabel && (
        <div className="text-xs opacity-60 mt-1">{changeLabel}</div>
      )}
    </div>
  )
}
