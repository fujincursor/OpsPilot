import { useState } from 'react'
import type { TestCase, TestResult, TestResultStatus } from '../../types'
import TestResultItem from './TestResultItem'

interface TestCaseListProps {
  testCases: TestCase[]
  results: TestResult[]
}

type FilterType = 'all' | TestResultStatus

export default function TestCaseList({ testCases, results }: TestCaseListProps) {
  const [filter, setFilter] = useState<FilterType>('all')
  const [searchTerm, setSearchTerm] = useState('')

  const resultMap = new Map<string, TestResult>()
  results.forEach((r) => resultMap.set(r.test_case_id, r))

  const filteredCases = testCases.filter((tc) => {
    const result = resultMap.get(tc.id)
    const status = result?.status ?? 'skipped'

    if (filter !== 'all' && status !== filter) return false

    if (searchTerm) {
      const search = searchTerm.toLowerCase()
      return (
        tc.name.toLowerCase().includes(search) ||
        tc.description.toLowerCase().includes(search)
      )
    }

    return true
  })

  const passedCount = results.filter((r) => r.status === 'passed').length
  const failedCount = results.filter((r) => r.status === 'failed').length
  const skippedCount = testCases.length - results.length + results.filter((r) => r.status === 'skipped').length

  const filters: { key: FilterType; label: string; count: number; className: string }[] = [
    { key: 'all', label: '全部', count: testCases.length, className: 'bg-gray-100 text-gray-700' },
    { key: 'passed', label: '通过', count: passedCount, className: 'bg-green-100 text-green-700' },
    { key: 'failed', label: '失败', count: failedCount, className: 'bg-red-100 text-red-700' },
    { key: 'skipped', label: '跳过', count: skippedCount, className: 'bg-gray-100 text-gray-500' },
  ]

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <span>🧪</span>
            测试用例
          </h3>
          <span className="text-sm text-gray-500">{testCases.length} 个用例</span>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1 p-1 bg-gray-100 rounded-lg">
            {filters.map((f) => (
              <button
                key={f.key}
                onClick={() => setFilter(f.key)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  filter === f.key
                    ? `${f.className}`
                    : 'text-gray-500 hover:bg-gray-200'
                }`}
              >
                {f.label}
                <span className="ml-1 opacity-70">({f.count})</span>
              </button>
            ))}
          </div>

          <div className="flex-1 min-w-[200px] max-w-sm">
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                🔍
              </span>
              <input
                type="text"
                placeholder="搜索测试用例..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-3 max-h-[600px] overflow-y-auto">
        {filteredCases.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <span className="text-3xl mb-2 block">📭</span>
            没有找到匹配的测试用例
          </div>
        ) : (
          filteredCases.map((tc) => (
            <TestResultItem
              key={tc.id}
              testCase={tc}
              result={resultMap.get(tc.id)}
            />
          ))
        )}
      </div>
    </div>
  )
}
