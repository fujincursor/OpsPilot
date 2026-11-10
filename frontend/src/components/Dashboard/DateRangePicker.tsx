import { useState } from 'react'
import type { DateRange } from '../../types'

interface DateRangePickerProps {
  value: DateRange
  onChange: (range: DateRange) => void
}

type PresetKey = '7d' | '14d' | '30d' | '90d' | 'custom'

const presets: { key: PresetKey; label: string; days: number }[] = [
  { key: '7d', label: '近 7 天', days: 7 },
  { key: '14d', label: '近 14 天', days: 14 },
  { key: '30d', label: '近 30 天', days: 30 },
  { key: '90d', label: '近 90 天', days: 90 },
]

function getDateRange(days: number): DateRange {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - days)
  return {
    start: start.toISOString().split('T')[0],
    end: end.toISOString().split('T')[0],
  }
}

export default function DateRangePicker({ value, onChange }: DateRangePickerProps) {
  const [showCustom, setShowCustom] = useState(false)
  const [activePreset, setActivePreset] = useState<PresetKey>('7d')

  const handlePresetClick = (preset: { key: PresetKey; days: number }) => {
    setActivePreset(preset.key)
    setShowCustom(false)
    onChange(getDateRange(preset.days))
  }

  const handleCustomClick = () => {
    setActivePreset('custom')
    setShowCustom(!showCustom)
  }

  const handleStartChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ ...value, start: e.target.value })
  }

  const handleEndChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ ...value, end: e.target.value })
  }

  return (
    <div className="relative">
      <div className="flex items-center gap-2 flex-wrap">
        {presets.map((preset) => (
          <button
            key={preset.key}
            onClick={() => handlePresetClick(preset)}
            className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
              activePreset === preset.key
                ? 'bg-primary text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {preset.label}
          </button>
        ))}
        <button
          onClick={handleCustomClick}
          className={`px-3 py-1.5 text-sm rounded-lg transition-colors flex items-center gap-1.5 ${
            activePreset === 'custom'
              ? 'bg-primary text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          📅 自定义
        </button>
      </div>
      
      {showCustom && (
        <div className="absolute top-full mt-2 left-0 bg-white rounded-lg shadow-lg border border-gray-200 p-4 z-10">
          <div className="flex items-center gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">开始日期</label>
              <input
                type="date"
                value={value.start}
                onChange={handleStartChange}
                className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
              />
            </div>
            <span className="text-gray-400 mt-4">—</span>
            <div>
              <label className="block text-xs text-gray-500 mb-1">结束日期</label>
              <input
                type="date"
                value={value.end}
                onChange={handleEndChange}
                className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
              />
            </div>
          </div>
          <button
            onClick={() => setShowCustom(false)}
            className="mt-3 w-full py-1.5 text-sm bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors"
          >
            应用
          </button>
        </div>
      )}
      
      {activePreset !== 'custom' && (
        <div className="mt-2 text-xs text-gray-400">
          {value.start} 至 {value.end}
        </div>
      )}
    </div>
  )
}
