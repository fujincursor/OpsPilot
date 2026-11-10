import type { FeatureDesignSolution } from '../../types'

interface FeatureDesignViewProps {
  solution: FeatureDesignSolution
}

const methodColors: Record<string, string> = {
  GET: 'bg-green-100 text-green-700',
  POST: 'bg-blue-100 text-blue-700',
  PUT: 'bg-amber-100 text-amber-700',
  PATCH: 'bg-purple-100 text-purple-700',
  DELETE: 'bg-red-100 text-red-700',
}

export default function FeatureDesignView({ solution }: FeatureDesignViewProps) {
  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-xl border border-purple-200 overflow-hidden">
        <div className="px-4 py-3 bg-purple-100/50 border-b border-purple-200">
          <div className="flex items-center gap-2">
            <span>🏗️</span>
            <span className="font-semibold text-purple-800">架构设计</span>
          </div>
        </div>
        <div className="p-4">
          <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed mb-4">
            {solution.architecture.overview}
          </p>
          {solution.architecture.components.length > 0 && (
            <div className="space-y-3">
              <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                组件设计
              </div>
              {solution.architecture.components.map((component, index) => (
                <div
                  key={index}
                  className="p-3 bg-white/60 rounded-lg border border-purple-100"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="w-2 h-2 bg-purple-500 rounded-full" />
                    <span className="font-medium text-gray-800">{component.name}</span>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{component.description}</p>
                  {component.responsibilities.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {component.responsibilities.map((resp, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 bg-purple-100 rounded text-xs text-purple-700"
                        >
                          {resp}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {solution.api_design.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
            <div className="flex items-center gap-2">
              <span>🔌</span>
              <span className="font-semibold text-gray-800">API 设计</span>
              <span className="px-2 py-0.5 bg-gray-200 rounded-full text-xs text-gray-600">
                {solution.api_design.length} 个接口
              </span>
            </div>
          </div>
          <div className="divide-y divide-gray-100">
            {solution.api_design.map((api, index) => (
              <div key={index} className="p-4">
                <div className="flex items-center gap-3 mb-2">
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-bold ${methodColors[api.method]}`}
                  >
                    {api.method}
                  </span>
                  <code className="text-sm font-mono text-gray-800">{api.endpoint}</code>
                </div>
                <p className="text-sm text-gray-600 mb-3">{api.description}</p>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                  {api.request_body && (
                    <div>
                      <div className="text-xs text-gray-500 mb-1.5">Request Body</div>
                      <pre className="p-3 bg-gray-900 rounded-lg overflow-x-auto">
                        <code className="text-xs text-gray-100 font-mono whitespace-pre">
                          {api.request_body}
                        </code>
                      </pre>
                    </div>
                  )}
                  {api.response_body && (
                    <div>
                      <div className="text-xs text-gray-500 mb-1.5">Response Body</div>
                      <pre className="p-3 bg-gray-900 rounded-lg overflow-x-auto">
                        <code className="text-xs text-gray-100 font-mono whitespace-pre">
                          {api.response_body}
                        </code>
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {solution.database_changes.length > 0 && (
        <div className="bg-gradient-to-br from-cyan-50 to-blue-50 rounded-xl border border-cyan-200 overflow-hidden">
          <div className="px-4 py-3 bg-cyan-100/50 border-b border-cyan-200">
            <div className="flex items-center gap-2">
              <span>🗃️</span>
              <span className="font-semibold text-cyan-800">数据库变更</span>
              <span className="px-2 py-0.5 bg-cyan-200 rounded-full text-xs text-cyan-700">
                {solution.database_changes.length} 项变更
              </span>
            </div>
          </div>
          <div className="divide-y divide-cyan-100">
            {solution.database_changes.map((change, index) => (
              <div key={index} className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-0.5 bg-cyan-200 rounded text-xs font-medium text-cyan-700">
                    {change.type.replace('_', ' ').toUpperCase()}
                  </span>
                  <code className="text-sm font-mono text-gray-800">{change.table_name}</code>
                </div>
                <p className="text-sm text-gray-600 mb-3">{change.description}</p>
                {change.sql && (
                  <pre className="p-3 bg-gray-900 rounded-lg overflow-x-auto">
                    <code className="text-sm text-gray-100 font-mono whitespace-pre">
                      {change.sql}
                    </code>
                  </pre>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {solution.dependencies.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
            <div className="flex items-center gap-2">
              <span>📦</span>
              <span className="font-semibold text-gray-800">依赖项</span>
            </div>
          </div>
          <div className="p-4">
            <div className="flex flex-wrap gap-2">
              {solution.dependencies.map((dep, index) => (
                <span
                  key={index}
                  className="px-3 py-1.5 bg-gray-100 rounded-lg text-sm text-gray-700 font-mono"
                >
                  {dep}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
