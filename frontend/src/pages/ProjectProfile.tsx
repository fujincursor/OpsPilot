import { FormEvent, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { knowledgeService, projectService } from '../services'
import type { ProjectProfile as Profile } from '../types'

const emptyProfile = (): Profile => ({
  overview: '',
  architecture: '',
  directory_layout: '',
  key_modules: '',
  config_notes: '',
  runbook: '',
})

const fields: Array<{ key: keyof Profile; label: string }> = [
  { key: 'overview', label: '项目概述' },
  { key: 'architecture', label: '架构说明' },
  { key: 'directory_layout', label: '目录结构' },
  { key: 'key_modules', label: '关键模块' },
  { key: 'config_notes', label: '配置说明' },
  { key: 'runbook', label: 'Runbook' },
]

export default function ProjectProfile() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [editing, setEditing] = useState(false)
  const [profile, setProfile] = useState<Profile>(emptyProfile())
  const [saved, setSaved] = useState<Profile>(emptyProfile())
  const [knowledgeReady, setKnowledgeReady] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!id) return
    projectService.getProject(id).then((project) => {
      const next = { ...emptyProfile(), ...project.profile }
      setProfile(next)
      setSaved(next)
    }).catch(() => setProfile(emptyProfile()))
    knowledgeService.getReadyStatus(id).then((status) => setKnowledgeReady(status.is_ready)).catch(() => setKnowledgeReady(false))
  }, [id])

  const profileReady = Boolean(profile.overview.trim() && (profile.architecture.trim() || profile.directory_layout.trim()))
  const ready = profileReady && knowledgeReady

  const save = async (event: FormEvent) => {
    event.preventDefault()
    if (!id) return
    await projectService.updateProject(id, { profile })
    setSaved(profile)
    setEditing(false)
    setMessage('项目资料已保存')
  }

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <div className="max-w-3xl mx-auto">
        <button type="button" onClick={() => navigate(`/projects/${id}`)} className="mb-4 text-sm text-gray-600">← 返回项目</button>
        <div className="mb-4 flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-gray-800">项目信息</h1>
          <span className={`rounded-full px-3 py-1 text-xs ${ready ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
            {ready ? '可以提交需求' : '资料未就绪'}
          </span>
        </div>
        {!ready && (
          <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            提交需求前需要知识库就绪，并填写项目概述，以及架构说明或目录结构。
            {!knowledgeReady && ' 当前知识库未就绪。'}
            {!profileReady && ' 当前项目资料不完整。'}
          </div>
        )}
        {editing ? (
          <form onSubmit={save} className="space-y-4 rounded-xl border border-gray-200 bg-white p-5">
            {fields.map((field) => (
              <label key={field.key} className="block text-sm text-gray-600">
                {field.label}
                <textarea
                  value={profile[field.key]}
                  onChange={(event) => setProfile({ ...profile, [field.key]: event.target.value })}
                  className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2"
                  rows={4}
                />
              </label>
            ))}
            <div className="flex gap-2">
              <button type="submit" className="rounded-lg bg-primary px-4 py-2 text-sm text-white">保存</button>
              <button type="button" onClick={() => { setProfile(saved); setEditing(false) }} className="rounded-lg bg-gray-100 px-4 py-2 text-sm">取消</button>
            </div>
          </form>
        ) : (
          <div className="space-y-4">
            {fields.map((field) => (
              <section key={field.key} className="rounded-xl border border-gray-200 bg-white p-4">
                <h2 className="mb-2 text-sm font-semibold text-gray-700">{field.label}</h2>
                <p className="whitespace-pre-wrap text-sm text-gray-600">{profile[field.key] || '未填写'}</p>
              </section>
            ))}
            <button type="button" onClick={() => setEditing(true)} className="rounded-lg bg-primary px-4 py-2 text-sm text-white">编辑</button>
          </div>
        )}
        {message && <p className="mt-3 text-sm text-green-600">{message}</p>}
      </div>
    </div>
  )
}
