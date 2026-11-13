import { useState } from 'react'
import type { SandboxSettings, SandboxTestResult } from '../../types'

const images = ['python:3.11-slim', 'node:20-alpine', 'openjdk:17-slim']
const memoryChoices = [1024, 2048, 4096, 8192]
const cpuChoices = [1, 2, 4]
const tools = [
  { id: 'git', label: 'git' },
  { id: 'curl', label: 'curl' },
  { id: 'jq', label: 'jq' },
  { id: 'kubectl', label: 'kubectl' },
  { id: 'docker-cli', label: 'docker-cli' },
]
const environments = [
  { id: 'docker', title: 'Docker AIO', detail: '本地 Docker', hint: '适合开发/测试', icon: '🐳' },
  { id: 'kubernetes', title: 'Kubernetes', detail: 'K8s Pod', hint: '适合生产环境', icon: '☸️' },
  { id: 'e2b', title: 'E2B Cloud', detail: '云端沙箱', hint: '按需使用', icon: '☁️' },
]

interface SandboxConfigPanelProps {
  sandbox: SandboxSettings
  testing: boolean
  result: SandboxTestResult | null
  onChange: (sandbox: SandboxSettings) => void
  onTest: () => void
  onCloseResult: () => void
}

function environmentId(backend: string): string {
  if (backend === 'kubernetes') return 'kubernetes'
  if (backend === 'e2b') return 'e2b'
  return 'docker'
}

function Choice({
  active,
  children,
  onClick,
}: {
  active: boolean
  children: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-md px-3 py-1.5 text-sm ${active ? 'bg-primary text-white' : 'bg-white text-gray-700 border border-gray-200'}`}
    >
      {children}
    </button>
  )
}

export default function SandboxConfigPanel({
  sandbox,
  testing,
  result,
  onChange,
  onTest,
  onCloseResult,
}: SandboxConfigPanelProps) {
  const [domain, setDomain] = useState('')
  const [showPackages, setShowPackages] = useState(false)
  const [showSecurity, setShowSecurity] = useState(false)
  const selected = environmentId(sandbox.backend)
  const imageOptions = images.includes(sandbox.image) ? images : [sandbox.image, ...images]
  const memories = memoryChoices.includes(sandbox.memory_mb) ? memoryChoices : [sandbox.memory_mb, ...memoryChoices]
  const cpus = cpuChoices.includes(sandbox.cpu) ? cpuChoices : [sandbox.cpu, ...cpuChoices]

  const patch = (partial: Partial<SandboxSettings>) => onChange({ ...sandbox, ...partial })
  const toggleTool = (id: string) => {
    const current = sandbox.system_tools || []
    patch({ system_tools: current.includes(id) ? current.filter((item) => item !== id) : [...current, id] })
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-gray-800">Sandbox 配置</h2>
        <p className="mt-1 text-sm text-gray-500">配置代码执行的隔离环境，Agent 将在此环境中运行代码检查和测试。</p>
      </div>

      <section className="rounded-lg border border-gray-200 p-4">
        <h3 className="mb-3 text-sm font-semibold text-gray-800">执行环境</h3>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          {environments.map((item) => {
            const active = selected === item.id
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => patch({ backend: item.id === 'docker' ? (sandbox.backend === 'docker' ? 'docker' : 'local') : item.id })}
                className={`rounded-lg px-4 py-5 text-center ${active ? 'border-2 border-primary bg-indigo-50' : 'border border-gray-200 bg-white hover:border-primary'}`}
              >
                <div className="text-2xl">{item.icon}</div>
                <div className="mt-2 text-sm font-semibold text-gray-800">{item.title}</div>
                <div className="mt-1 text-xs text-gray-500">{item.detail}</div>
                <div className="text-xs text-gray-400">{item.hint}</div>
              </button>
            )
          })}
        </div>
      </section>

      {selected === 'docker' && (
        <section className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-3 text-sm font-semibold text-gray-800">Docker AIO 配置</h3>
          <label className="block text-sm text-gray-600">基础镜像
            <select value={sandbox.image} onChange={(event) => patch({ image: event.target.value })} className="mt-1 w-full rounded-lg border border-gray-200 bg-white px-3 py-2">
              {imageOptions.map((image) => <option key={image} value={image}>{image}</option>)}
            </select>
          </label>
          <p className="mt-2 text-xs text-gray-500">推荐镜像：python:3.11-slim、node:20-alpine、openjdk:17-slim</p>
        </section>
      )}

      {selected === 'kubernetes' && (
        <section className="rounded-lg border border-gray-200 p-4 space-y-3">
          <h3 className="text-sm font-semibold text-gray-800">Kubernetes 配置</h3>
          <p className="text-sm text-gray-500">集群连接</p>
          <div className="space-y-2 text-sm text-gray-700">
            <label className="flex items-center gap-2">
              <input type="radio" checked={sandbox.kubeconfig_mode !== 'custom'} onChange={() => patch({ kubeconfig_mode: 'default' })} />
              使用默认 (~/.kube/config)
            </label>
            <label className="flex items-center gap-2">
              <input type="radio" checked={sandbox.kubeconfig_mode === 'custom'} onChange={() => patch({ kubeconfig_mode: 'custom' })} />
              自定义配置
            </label>
          </div>
          {sandbox.kubeconfig_mode === 'custom' && (
            <textarea
              value={sandbox.kubeconfig}
              onChange={(event) => patch({ kubeconfig: event.target.value })}
              rows={6}
              placeholder="apiVersion: v1"
              className="w-full rounded-lg border border-gray-200 px-3 py-2 font-mono text-xs"
            />
          )}
          <label className="block text-sm text-gray-600">Namespace
            <input value={sandbox.namespace} onChange={(event) => patch({ namespace: event.target.value })} placeholder="ops-agent-sandbox" className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2" />
          </label>
          <label className="block text-sm text-gray-600">Service Account
            <input value={sandbox.service_account} onChange={(event) => patch({ service_account: event.target.value })} placeholder="sandbox-runner" className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2" />
          </label>
        </section>
      )}

      {selected === 'e2b' && (
        <section className="rounded-lg border border-gray-200 p-4 space-y-3">
          <h3 className="text-sm font-semibold text-gray-800">E2B Cloud 配置</h3>
          <p className="text-sm text-gray-500">E2B 是按需使用的云端沙箱服务。</p>
          <label className="block text-sm text-gray-600">API Key
            <input type="password" value={sandbox.e2b_api_key} onChange={(event) => patch({ e2b_api_key: event.target.value })} className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2" />
          </label>
          <label className="block text-sm text-gray-600">模板 ID
            <select value={sandbox.e2b_template} onChange={(event) => patch({ e2b_template: event.target.value })} className="mt-1 w-full rounded-lg border border-gray-200 bg-white px-3 py-2">
              <option value="python-3.11">python-3.11</option>
              <option value="node-20">node-20</option>
            </select>
          </label>
          <p className="text-xs text-gray-500">获取 API Key：https://e2b.dev/dashboard</p>
        </section>
      )}

      <section className="rounded-lg border border-gray-200 p-4 space-y-4">
        <h3 className="text-sm font-semibold text-gray-800">资源限制</h3>
        <div>
          <div className="mb-2 text-sm text-gray-600">内存限制</div>
          <div className="flex flex-wrap gap-2">
            {memories.map((value) => (
              <Choice key={value} active={sandbox.memory_mb === value} onClick={() => patch({ memory_mb: value })}>
                {value % 1024 === 0 ? `${value / 1024}GB` : `${value}MB`}
              </Choice>
            ))}
          </div>
        </div>
        <div>
          <div className="mb-2 text-sm text-gray-600">CPU 限制</div>
          <div className="flex flex-wrap gap-2">
            {cpus.map((value) => (
              <Choice key={value} active={sandbox.cpu === value} onClick={() => patch({ cpu: value })}>
                {`${value}核`}
              </Choice>
            ))}
          </div>
        </div>
        <label className="block text-sm text-gray-600">执行超时
          <span className="mt-1 flex items-center gap-2">
            <input type="number" min={1} max={3600} value={sandbox.timeout_seconds} onChange={(event) => patch({ timeout_seconds: Number(event.target.value) })} className="w-32 rounded-lg border border-gray-200 px-3 py-2" />
            <span>秒（最大 3600 秒）</span>
          </span>
        </label>
        <label className="block text-sm text-gray-600">磁盘空间
          <span className="mt-1 flex items-center gap-2">
            <input type="number" min={1} max={50} value={sandbox.disk_gb} onChange={(event) => patch({ disk_gb: Number(event.target.value) })} className="w-32 rounded-lg border border-gray-200 px-3 py-2" />
            <span>GB（最大 50 GB）</span>
          </span>
        </label>
      </section>

      <section className="rounded-lg border border-gray-200 p-4 space-y-3">
        <h3 className="text-sm font-semibold text-gray-800">网络策略</h3>
        {[
          ['disabled', '禁用网络（最安全）'],
          ['allowlist', '白名单模式（推荐）'],
          ['open', '允许所有（不推荐）'],
        ].map(([value, label]) => (
          <label key={value} className="flex items-center gap-2 text-sm text-gray-700">
            <input type="radio" checked={sandbox.network_policy === value} onChange={() => patch({ network_policy: value })} />
            {label}
          </label>
        ))}
        {sandbox.network_policy === 'allowlist' && (
          <div className="space-y-2">
            <div className="text-sm text-gray-600">允许访问的域名</div>
            {(sandbox.allowed_domains || []).map((item) => (
              <div key={item} className="flex items-center justify-between rounded-md border border-gray-200 px-3 py-2 text-sm">
                <span>{item}</span>
                <button type="button" onClick={() => patch({ allowed_domains: sandbox.allowed_domains.filter((domain) => domain !== item) })} className="text-xs text-red-600">删除</button>
              </div>
            ))}
            <div className="flex gap-2">
              <input value={domain} onChange={(event) => setDomain(event.target.value)} placeholder="例如 pypi.org" className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm" />
              <button
                type="button"
                onClick={() => {
                  const next = domain.trim()
                  if (!next || sandbox.allowed_domains.includes(next)) return
                  patch({ allowed_domains: [...sandbox.allowed_domains, next] })
                  setDomain('')
                }}
                className="rounded-lg bg-gray-100 px-3 py-2 text-sm"
              >
                添加域名
              </button>
            </div>
          </div>
        )}
      </section>

      <section className="rounded-lg border border-gray-200 p-4">
        <button type="button" onClick={() => setShowPackages((open) => !open)} className="flex w-full items-center justify-between text-sm font-semibold text-gray-800">
          预装依赖
          <span className="text-xs font-normal text-gray-500">{showPackages ? '收起' : '展开'}</span>
        </button>
        {showPackages && (
          <div className="mt-3 space-y-3">
            <p className="text-xs text-gray-500">这里只保存期望预装的内容，当前执行环境还不会自动安装。</p>
            <label className="block text-sm text-gray-600">Python 依赖（requirements.txt）
              <textarea value={sandbox.python_requirements} onChange={(event) => patch({ python_requirements: event.target.value })} rows={4} placeholder={'pytest>=7.0.0\npylint>=2.15.0'} className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 font-mono text-xs" />
            </label>
            <div className="flex flex-wrap gap-4 text-sm text-gray-700">
              {tools.map((tool) => (
                <label key={tool.id} className="flex items-center gap-2">
                  <input type="checkbox" checked={(sandbox.system_tools || []).includes(tool.id)} onChange={() => toggleTool(tool.id)} />
                  {tool.label}
                </label>
              ))}
            </div>
          </div>
        )}
      </section>

      <section className="rounded-lg border border-gray-200 p-4">
        <button type="button" onClick={() => setShowSecurity((open) => !open)} className="flex w-full items-center justify-between text-sm font-semibold text-gray-800">
          安全配置
          <span className="text-xs font-normal text-gray-500">{showSecurity ? '收起' : '展开'}</span>
        </button>
        {showSecurity && (
          <div className="mt-3 space-y-2 text-sm text-gray-700">
            <label className="flex items-center gap-2"><input type="checkbox" checked={sandbox.run_as_non_root} onChange={(event) => patch({ run_as_non_root: event.target.checked })} />以非 root 用户运行</label>
            <label className="flex items-center gap-2"><input type="checkbox" checked={sandbox.disable_privileged} onChange={(event) => patch({ disable_privileged: event.target.checked })} />禁用特权模式</label>
            <label className="flex items-center gap-2"><input type="checkbox" checked={sandbox.read_only_root} onChange={(event) => patch({ read_only_root: event.target.checked })} />只读文件系统（除工作目录外）</label>
            <label className="flex items-center gap-2"><input type="checkbox" checked={sandbox.disable_setuid} onChange={(event) => patch({ disable_setuid: event.target.checked })} />禁用 setuid/setgid</label>
            <label className="flex items-center gap-2"><input type="checkbox" checked={sandbox.seccomp} onChange={(event) => patch({ seccomp: event.target.checked })} />启用 Seccomp 配置文件</label>
          </div>
        )}
      </section>

      <div className="flex justify-end gap-2">
        <button type="button" onClick={onTest} disabled={testing} className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm text-gray-700 disabled:opacity-50">
          {testing ? '测试中...' : '测试配置'}
        </button>
        <button type="submit" className="rounded-lg bg-primary px-4 py-2 text-sm text-white">保存配置</button>
      </div>

      {result && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-xl bg-white p-5 shadow-lg">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-base font-semibold text-gray-800">配置测试结果</h3>
              <button type="button" onClick={onCloseResult} className="text-sm text-gray-500">关闭</button>
            </div>
            <p className={`mb-3 text-sm ${result.ok ? 'text-green-700' : 'text-amber-700'}`}>{result.message}</p>
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-200 text-gray-500">
                  <th className="py-2 font-medium">测试项</th>
                  <th className="py-2 font-medium">结果</th>
                </tr>
              </thead>
              <tbody>
                {(result.checks || []).map((check) => (
                  <tr key={check.name} className="border-b border-gray-100">
                    <td className="py-2 text-gray-800">{check.name}</td>
                    <td className="py-2 text-gray-600">{check.ok ? '通过' : '未通过'} · {check.detail}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {result.output && (
              <pre className="mt-3 overflow-auto rounded-lg bg-gray-50 p-3 text-xs text-gray-700">{result.output}</pre>
            )}
            <div className="mt-4 text-right">
              <button type="button" onClick={onCloseResult} className="rounded-lg bg-primary px-4 py-2 text-sm text-white">确定</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
