import { useState } from 'react'
import type { SearchResult } from '../../types'

interface SearchTestProps {
  onSearch: (query: string) => Promise<SearchResult[]>
}

export default function SearchTest({ onSearch }: SearchTestProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setIsSearching(true)
    setHasSearched(true)
    try {
      const searchResults = await onSearch(query.trim())
      setResults(searchResults)
    } catch (error) {
      console.error('Search failed:', error)
      setResults([])
    } finally {
      setIsSearching(false)
    }
  }

  const highlightContent = (content: string, maxLength = 200): string => {
    if (content.length <= maxLength) return content
    return content.substring(0, maxLength) + '...'
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
        <span>🔍</span>
        知识检索测试
      </h3>

      <form onSubmit={handleSearch} className="mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="输入查询内容，测试知识检索..."
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
          <button
            type="submit"
            disabled={isSearching || !query.trim()}
            className="px-5 py-2.5 bg-primary hover:bg-primary-hover text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isSearching ? (
              <>
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                搜索中
              </>
            ) : (
              <>🔍 搜索</>
            )}
          </button>
        </div>
      </form>

      {hasSearched && (
        <div className="space-y-3">
          {isSearching ? (
            <div className="text-center py-8 text-gray-500">
              <div className="w-8 h-8 border-3 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              正在检索知识库...
            </div>
          ) : results.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-2">🔍</div>
              未找到相关内容
            </div>
          ) : (
            <>
              <div className="text-sm text-gray-500 mb-2">
                找到 {results.length} 条相关结果
              </div>
              {results.map((result) => (
                <div
                  key={result.document_id}
                  className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-medium text-gray-800">
                      {result.title}
                    </h4>
                    <div className="flex items-center gap-2 flex-shrink-0 ml-4">
                      <span className="text-xs text-gray-400 bg-gray-200 px-2 py-0.5 rounded">
                        {result.knowledge_base_name}
                      </span>
                      <span
                        className={`text-xs font-medium px-2 py-0.5 rounded ${
                          result.score > 0.8
                            ? 'bg-green-100 text-green-600'
                            : result.score > 0.6
                            ? 'bg-yellow-100 text-yellow-600'
                            : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        相关度: {(result.score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 leading-relaxed">
                    {highlightContent(result.content)}
                  </p>
                </div>
              ))}
            </>
          )}
        </div>
      )}

      {!hasSearched && (
        <div className="text-center py-8 text-gray-400">
          <div className="text-4xl mb-2">💡</div>
          输入问题测试知识库检索效果
        </div>
      )}
    </div>
  )
}
