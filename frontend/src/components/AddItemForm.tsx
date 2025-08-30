import React, { useState } from 'react'
import { Button, Input } from './ui'
import { FileUpload, ImagePreview } from './ui/FileUpload'
import { ErrorMessage } from './ui/Alert'
import { layoutClasses } from '../utils/layout'

interface AddItemFormData {
  category: string
  color: string
  brand: string
  size: string
  tags: string
  notes: string
}

interface AddItemFormProps {
  onSubmit: (data: AddItemFormData & { files: File[] }) => Promise<void>
  loading?: boolean
  error?: string | null
}

const CATEGORIES = [
  'tops', 'bottoms', 'dresses', 'outerwear', 'shoes', 
  'accessories', 'underwear', 'activewear', 'formal', 'casual'
]

const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL', '28', '30', '32', '34', '36', '38', '6', '7', '8', '9', '10', '11', '12']

export const AddItemForm: React.FC<AddItemFormProps> = ({
  onSubmit,
  loading = false,
  error = null
}) => {
  const [formData, setFormData] = useState<AddItemFormData>({
    category: '',
    color: '',
    brand: '',
    size: '',
    tags: '',
    notes: ''
  })
  const [files, setFiles] = useState<File[]>([])

  const handleInputChange = (field: keyof AddItemFormData) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    setFormData(prev => ({ ...prev, [field]: e.target.value }))
  }

  const handleFileSelect = (fileList: FileList) => {
    const newFiles = Array.from(fileList)
    setFiles(prev => [...prev, ...newFiles])
  }

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (files.length === 0) {
      return
    }
    await onSubmit({ ...formData, files })
  }

  const isValid = files.length > 0 && formData.category && formData.color

  return (
    <form onSubmit={handleSubmit} className={layoutClasses.form}>
      {/* Image Upload Section */}
      <div className={layoutClasses.formField}>
        <label className="block text-sm font-medium text-neutral-700 mb-2">
          Photos *
        </label>
        <FileUpload
          onFileSelect={handleFileSelect}
          multiple
          disabled={loading}
        />
        {files.length > 0 && (
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3 mt-3">
            {files.map((file, index) => (
              <ImagePreview
                key={`${file.name}-${index}`}
                file={file}
                onRemove={() => removeFile(index)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Basic Information */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className={layoutClasses.formField}>
          <label className="block text-sm font-medium text-neutral-700">
            Category *
          </label>
          <select
            value={formData.category}
            onChange={handleInputChange('category')}
            required
            disabled={loading}
            className="w-full border border-neutral-300 rounded-sm px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-neutral-500 focus:border-neutral-500 bg-white"
          >
            <option value="">Select category</option>
            {CATEGORIES.map(cat => (
              <option key={cat} value={cat}>
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div className={layoutClasses.formField}>
          <label className="block text-sm font-medium text-neutral-700">
            Color *
          </label>
          <Input
            type="text"
            value={formData.color}
            onChange={handleInputChange('color')}
            placeholder="e.g., Navy Blue, Red, Black"
            required
            disabled={loading}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className={layoutClasses.formField}>
          <label className="block text-sm font-medium text-neutral-700">
            Brand <span className="text-neutral-500 font-normal">(Optional)</span>
          </label>
          <Input
            type="text"
            value={formData.brand}
            onChange={handleInputChange('brand')}
            placeholder="e.g., Nike, Zara, H&M"
            disabled={loading}
          />
        </div>

        <div className={layoutClasses.formField}>
          <label className="block text-sm font-medium text-neutral-700">
            Size <span className="text-neutral-500 font-normal">(Optional)</span>
          </label>
          <select
            value={formData.size}
            onChange={handleInputChange('size')}
            disabled={loading}
            className="w-full border border-neutral-300 rounded-sm px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-neutral-500 focus:border-neutral-500 bg-white"
          >
            <option value="">Select size</option>
            {SIZES.map(size => (
              <option key={size} value={size}>{size}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Tags and Notes */}
      <div className={layoutClasses.formField}>
        <label className="block text-sm font-medium text-neutral-700">
          Tags <span className="text-neutral-500 font-normal">(Optional)</span>
        </label>
        <Input
          type="text"
          value={formData.tags}
          onChange={handleInputChange('tags')}
          placeholder="e.g., formal, work, summer, casual (comma-separated)"
          disabled={loading}
        />
        <div className="text-xs text-neutral-500 mt-1">
          Separate multiple tags with commas
        </div>
      </div>

      <div className={layoutClasses.formField}>
        <label className="block text-sm font-medium text-neutral-700">
          Notes <span className="text-neutral-500 font-normal">(Optional)</span>
        </label>
        <textarea
          value={formData.notes}
          onChange={handleInputChange('notes')}
          placeholder="Any additional notes about this item..."
          disabled={loading}
          className="w-full border border-neutral-300 rounded-sm px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-neutral-500 focus:border-neutral-500 resize-y min-h-[80px]"
        />
      </div>

      <ErrorMessage error={error} />

      <Button
        type="submit"
        disabled={loading || !isValid}
        className="w-full sm:w-auto"
      >
        {loading ? 'Adding Item...' : 'Add to Closet'}
      </Button>
    </form>
  )
}
