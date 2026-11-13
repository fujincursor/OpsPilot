import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { TestCase, TestResult, TestResultStatus } from '../../types'
import TestStatusBadge from './TestStatusBadge'

interface TestResultItemProps {
  testCase: TestCase
  result?: TestResult
}

const typeLabels: Record<string, string> = {
  unit: '单元测试',
  integration: '集成测试',
  e2e: 'E2E测试',
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

function tableCells(line: string): string[] {
  const trimmed = line.trim()
  if (!trimmed.startsWith('|')) return []
  const normalized = trimmed.endsWith('|') ? trimmed : `${trimmed}|`
  return normalized.slice(1, -1).split('|').map((cell) => cell.trim()).filter((cell) => cell.length > 0)
}

function repairTables(text: string): string {
  const lines = text.replace(/\r\n/g, '\n').split('\n')
  const repaired: string[] = []
  for (let index = 0; index < lines.length; index += 1) {
    const cells = tableCells(lines[index])
    const next = lines[index + 1]
    const separator = next === undefined ? [] : tableCells(next)
    const broken = next !== undefined
      && next.trim().startsWith('|')
      && /^[\s|:-]+$/.test(next.trim())
      && (separator.length < cells.length || separator.some((cell) => !/^:?-{3,}:?$/.test(cell)))
    if (cells.length >= 2 && broken) {
      repaired.push(lines[index])
      repaired.push(`| ${cells.map(() => '---').join(' | ')} |`)
      index += 1
      continue
    }
    repaired.push(lines[index])
  }
  return repaired.join('\n')
}

export function MarkdownBlock({ text }: { text: string }) {
  return (
    <div className="markdown-body overflow-x-auto text-sm text-gray-700">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{repairTables(text)}</ReactMarkdown>
    </div>
  )
}

function getStatusIcon(status: TestResultStatus): string {
  switch (status) {
    case 'passed':
      return '✅'
    case 'failed':
      return '❌'
    case 'skipped':
      return '⏭️'
  }
}

export default function TestResultItem({ testCase, result }: TestResultItemProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const status = result?.status ?? 'skipped'
  const hasFailed = status === 'failed'

  return (
    <div
      className={`border rounded-lg overflow-hidden transition-all ${
        hasFailed ? 'border-red-200 bg-red-50/50' : 'border-gray-200 bg-white'
      }`}
    >
      <div
        className={`flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
          hasFailed ? 'hover:bg-red-50' : ''
        }`}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <span className="text-lg">{getStatusIcon(status)}</span>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-medium text-gray-800">{testCase.name}</span>
              <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">
                {typeLabels[testCase.type] || testCase.type}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {result && (
            <span className="text-sm text-gray-500">{formatDuration(result.duration_ms ?? result.duration ?? 0)}</span>
          )}
          <TestStatusBadge status={status} size="sm" />
          <span
            className={`text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          >
            ▼
          </span>
        </div>
      </div>

      {testCase.description && (
        <div className="border-t border-gray-100 px-4 py-3">
          <MarkdownBlock text={testCase.description} />
        </div>
      )}

      {isExpanded && (
        <div className="border-t border-gray-200 p-4 bg-gray-50">
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <div className="text-xs font-medium text-gray-500 mb-1">预期结果</div>
              <div className="bg-white rounded p-2 border border-gray-200">
                <MarkdownBlock text={testCase.expected_result || ''} />
              </div>
            </div>
            {result && (
              <div>
                <div className="text-xs font-medium text-gray-500 mb-1">实际结果</div>
                <div className="text-sm text-gray-700 bg-white rounded p-2 border border-gray-200">
                  {result.actual_result}
                </div>
              </div>
            )}
          </div>

          {hasFailed && result?.error_message && (
            <div className="mt-4">
              <div className="text-xs font-medium text-red-600 mb-1 flex items-center gap-1">
                <span>⚠️</span>
                错误信息
              </div>
              <div className="bg-red-100 border border-red-200 rounded p-3 text-sm text-red-800 font-mono overflow-x-auto">
                {result.error_message}
              </div>
            </div>
          )}

          <div className="mt-4">
            <div className="text-xs font-medium text-gray-500 mb-1 flex items-center gap-1">
              <span>💻</span>
              测试代码
            </div>
            <pre className="bg-gray-800 text-gray-100 rounded p-3 text-sm overflow-x-auto">
              <code>{testCase.code}</code>
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
