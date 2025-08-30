import React from 'react'
import { cn } from '../../utils/cn'

interface FileUploadProps {
  onFileSelect: (files: FileList) => void
  accept?: string
  multiple?: boolean
  disabled?: boolean
  className?: string
  children?: React.ReactNode
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onFileSelect,
  accept = "image/*",
  multiple = false,
  disabled = false,
  className,
  children
}) => {
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      onFileSelect(files)
    }
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      onFileSelect(files)
    }
  }

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
  }

  return (
    <div
      className={cn(
        'border-2 border-dashed border-neutral-300 rounded-sm p-6 text-center transition-colors',
        'hover:border-neutral-400 hover:bg-neutral-50',
        disabled && 'opacity-50 cursor-not-allowed',
        !disabled && 'cursor-pointer',
        className
      )}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
    >
      <input
        type="file"
        accept={accept}
        multiple={multiple}
        disabled={disabled}
        onChange={handleFileChange}
        className="hidden"
        id="file-upload"
      />
      <label 
        htmlFor="file-upload" 
        className={cn(
          'block cursor-pointer',
          disabled && 'cursor-not-allowed'
        )}
      >
        {children || (
          <div className="space-y-2">
            <div className="text-sm text-neutral-600">
              {multiple ? 'Drop images here or click to browse' : 'Drop an image here or click to browse'}
            </div>
            <div className="text-xs text-neutral-500">
              Supports: JPG, PNG, GIF
            </div>
          </div>
        )}
      </label>
    </div>
  )
}

interface ImagePreviewProps {
  file: File
  onRemove: () => void
  className?: string
}

export const ImagePreview: React.FC<ImagePreviewProps> = ({
  file,
  onRemove,
  className
}) => {
  const [preview, setPreview] = React.useState<string>('')

  React.useEffect(() => {
    const url = URL.createObjectURL(file)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  return (
    <div className={cn('relative group', className)}>
      <div className="aspect-square bg-neutral-100 rounded-sm overflow-hidden">
        <img 
          src={preview} 
          alt={file.name}
          className="w-full h-full object-cover"
        />
      </div>
      <button
        onClick={onRemove}
        className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
        type="button"
      >
        ×
      </button>
      <div className="mt-1 text-xs text-neutral-600 truncate">
        {file.name}
      </div>
    </div>
  )
}
