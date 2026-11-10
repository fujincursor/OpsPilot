import { useState, useRef, useCallback } from 'react'

interface UploadAreaProps {
  onUpload: (file: File) => Promise<void>
  acceptedTypes?: string[]
}

interface UploadingFile {
  name: string
  progress: number
  status: 'uploading' | 'success' | 'error'
  error?: string
}

const defaultAcceptedTypes = [
  '.pdf',
  '.doc',
  '.docx',
  '.md',
  '.txt',
  '.json',
  '.yaml',
  '.yml',
]

export default function UploadArea({
  onUpload,
  acceptedTypes = defaultAcceptedTypes,
}: UploadAreaProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const uploadFile = async (file: File) => {
    const fileEntry: UploadingFile = {
      name: file.name,
      progress: 0,
      status: 'uploading',
    }

    setUploadingFiles((prev) => [...prev, fileEntry])

    try {
      const progressInterval = setInterval(() => {
        setUploadingFiles((prev) =>
          prev.map((f) =>
            f.name === file.name && f.status === 'uploading'
              ? { ...f, progress: Math.min(f.progress + 10, 90) }
              : f
          )
        )
      }, 200)

      await onUpload(file)

      clearInterval(progressInterval)

      setUploadingFiles((prev) =>
        prev.map((f) =>
          f.name === file.name
            ? { ...f, progress: 100, status: 'success' }
            : f
        )
      )

      setTimeout(() => {
        setUploadingFiles((prev) =>
          prev.filter((f) => f.name !== file.name)
        )
      }, 2000)
    } catch (error) {
      setUploadingFiles((prev) =>
        prev.map((f) =>
          f.name === file.name
            ? {
                ...f,
                status: 'error',
                error: error instanceof Error ? error.message : '上传失败',
              }
            : f
        )
      )
    }
  }

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragging(false)

      const files = Array.from(e.dataTransfer.files)
      for (const file of files) {
        await uploadFile(file)
      }
    },
    [onUpload]
  )

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    for (const file of files) {
      await uploadFile(file)
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className="space-y-4">
      <div
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={handleClick}
        className={`
          border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
          ${
            isDragging
              ? 'border-primary bg-primary-light'
              : 'border-gray-300 hover:border-primary hover:bg-gray-50'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={acceptedTypes.join(',')}
          onChange={handleFileSelect}
          className="hidden"
        />

        <div className="text-4xl mb-3">
          {isDragging ? '📥' : '📤'}
        </div>

        <h4 className="text-base font-medium text-gray-800 mb-1">
          {isDragging ? '释放文件以上传' : '拖拽文件到此处上传'}
        </h4>
        <p className="text-sm text-gray-500 mb-3">
          或点击选择文件
        </p>
        <p className="text-xs text-gray-400">
          支持格式：{acceptedTypes.join(', ')}
        </p>
      </div>

      {uploadingFiles.length > 0 && (
        <div className="space-y-2">
          {uploadingFiles.map((file) => (
            <div
              key={file.name}
              className="bg-white rounded-lg border border-gray-200 p-3"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span>📄</span>
                  <span className="text-sm font-medium text-gray-800 truncate max-w-xs">
                    {file.name}
                  </span>
                </div>
                <span
                  className={`text-xs font-medium ${
                    file.status === 'success'
                      ? 'text-green-600'
                      : file.status === 'error'
                      ? 'text-red-600'
                      : 'text-blue-600'
                  }`}
                >
                  {file.status === 'success'
                    ? '✓ 上传成功'
                    : file.status === 'error'
                    ? `✕ ${file.error}`
                    : `${file.progress}%`}
                </span>
              </div>
              {file.status === 'uploading' && (
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div
                    className="bg-primary h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${file.progress}%` }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
