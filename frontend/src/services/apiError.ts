export function readApiError(error: unknown, fallback: string): string {
  const err = error as {
    code?: string
    message?: string
    response?: { status?: number; data?: { detail?: unknown } }
  }
  if (err?.code === 'ECONNABORTED') {
    return '生成请求超时，页面没有等到服务端结果。失败原因会写在这张需求上，刷新后仍可查看。'
  }
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail)) {
    const text = detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object' && 'msg' in item) return String((item as { msg: unknown }).msg)
        return ''
      })
      .filter(Boolean)
      .join('；')
    if (text) return text
  }
  if (err?.response?.status) return `服务返回 ${err.response.status}，没有附带失败原因。`
  if (typeof err?.message === 'string' && err.message.trim()) return err.message
  return fallback
}
