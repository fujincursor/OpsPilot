import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authService } from '../services/authService'

export default function Login() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await authService.login(username.trim(), password)
      navigate('/', { replace: true })
    } catch {
      setError('用户名或密码不正确')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <form onSubmit={handleSubmit} className="w-full max-w-sm bg-white border border-gray-200 rounded-xl shadow-sm p-6">
        <div className="text-2xl mb-2">🚀</div>
        <h1 className="text-xl font-semibold text-gray-800">OpsPilot</h1>
        <p className="text-sm text-gray-500">运维领航</p>
        <p className="text-sm text-gray-500 mt-1 mb-6">使用账号登录后查看接口中的真实数据。</p>
        <label className="block text-sm text-gray-700 mb-1">用户名</label>
        <input
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          className="w-full mb-4 px-3 py-2 border border-gray-300 rounded-lg text-sm"
          autoComplete="username"
          required
        />
        <label className="block text-sm text-gray-700 mb-1">密码</label>
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="w-full mb-4 px-3 py-2 border border-gray-300 rounded-lg text-sm"
          autoComplete="current-password"
          required
        />
        {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="w-full py-2.5 bg-primary text-white rounded-lg text-sm font-medium disabled:opacity-60"
        >
          {submitting ? '登录中...' : '登录'}
        </button>
        <p className="text-xs text-gray-400 mt-4">默认账号：admin / admin123</p>
      </form>
    </div>
  )
}
