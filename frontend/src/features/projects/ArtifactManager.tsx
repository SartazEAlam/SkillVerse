import React, { useState, useRef } from 'react'
import {
  Upload,
  FileText,
  FileArchive,
  FileImage,
  FileCode,
  Download,
  Trash2,
  AlertCircle,
  Eye,
  Lock,
  Loader2,
  HardDrive,
} from 'lucide-react'
import type { Artifact } from '../../types/project'
import { projectApi } from '../../services/projectApi'
import { ApiError } from '../../services/api'

const ALLOWED_EXTENSIONS = [
  '.zip',
  '.tar.gz',
  '.tgz',
  '.pdf',
  '.png',
  '.jpg',
  '.jpeg',
  '.webp',
  '.txt',
  '.md',
  '.json',
  '.csv',
]

const BLOCKED_EXTENSIONS = [
  '.exe',
  '.bat',
  '.cmd',
  '.sh',
  '.bash',
  '.ps1',
  '.py',
  '.pyw',
  '.js',
  '.mjs',
  '.cjs',
  '.ts',
  '.html',
  '.htm',
  '.xhtml',
  '.php',
  '.asp',
  '.aspx',
  '.jsp',
  '.dll',
  '.so',
  '.dylib',
  '.vbs',
  '.jar',
  '.msi',
]

const MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024 // 20 MB
const MAX_AGGREGATE_BYTES = 50 * 1024 * 1024 // 50 MB
const MAX_ARTIFACTS_COUNT = 10

interface ArtifactManagerProps {
  submissionId: string
  artifacts: Artifact[]
  isDraft: boolean
  onArtifactsChange: (artifacts: Artifact[]) => void
}

export const ArtifactManager: React.FC<ArtifactManagerProps> = ({
  submissionId,
  artifacts,
  isDraft,
  onArtifactsChange,
}) => {
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<string | null>(null)
  const [isPublic, setIsPublic] = useState(false)
  const [validationError, setValidationError] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const aggregateBytes = artifacts.reduce((acc, a) => acc + a.file_size_bytes, 0)
  const aggregateMb = (aggregateBytes / (1024 * 1024)).toFixed(1)
  const aggregatePct = Math.min(100, Math.round((aggregateBytes / MAX_AGGREGATE_BYTES) * 100))

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const getFileIcon = (filename: string) => {
    const lower = filename.toLowerCase()
    if (lower.endsWith('.zip') || lower.endsWith('.tar.gz') || lower.endsWith('.tgz')) {
      return <FileArchive className="h-4 w-4 text-accent-cyan" aria-hidden="true" />
    }
    if (
      lower.endsWith('.png') ||
      lower.endsWith('.jpg') ||
      lower.endsWith('.jpeg') ||
      lower.endsWith('.webp')
    ) {
      return <FileImage className="h-4 w-4 text-accent-violet" aria-hidden="true" />
    }
    if (lower.endsWith('.json') || lower.endsWith('.csv')) {
      return <FileCode className="h-4 w-4 text-state-warning" aria-hidden="true" />
    }
    return <FileText className="h-4 w-4 text-text-secondary" aria-hidden="true" />
  }

  const validateFile = (file: File): string | null => {
    const filename = file.name.toLowerCase()

    // 1. Check for blocked extensions
    for (const blocked of BLOCKED_EXTENSIONS) {
      if (filename.endsWith(blocked)) {
        return `Files with extension "${blocked}" are restricted for security reasons. Executables, scripts, and active code files cannot be uploaded directly. Please archive your repository or code into a .zip file.`
      }
    }

    // 2. Check for allowed extensions
    const isAllowed = ALLOWED_EXTENSIONS.some((ext) => filename.endsWith(ext))
    if (!isAllowed) {
      return `File type not supported. Allowed formats: ZIP, TAR.GZ, PDF, PNG, JPG, WEBP, TXT, MD, JSON, CSV.`
    }

    // 3. Individual size check (20MB)
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return `File "${file.name}" exceeds the individual limit of 20 MB (${(file.size / (1024 * 1024)).toFixed(1)} MB).`
    }

    // 4. Artifact count limit (10)
    if (artifacts.length >= MAX_ARTIFACTS_COUNT) {
      return `Maximum limit of ${MAX_ARTIFACTS_COUNT} deliverable artifacts reached for this submission.`
    }

    // 5. Aggregate size limit (50MB)
    if (aggregateBytes + file.size > MAX_AGGREGATE_BYTES) {
      return `Uploading "${file.name}" would exceed the total deliverable quota of 50 MB (Current total: ${aggregateMb} MB).`
    }

    return null
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setValidationError(null)
    setUploadError(null)

    const error = validateFile(file)
    if (error) {
      setValidationError(error)
      if (fileInputRef.current) fileInputRef.current.value = ''
      return
    }

    try {
      setIsUploading(true)
      setUploadProgress(`Uploading ${file.name}...`)
      const newArtifact = await projectApi.uploadArtifact(submissionId, file, isPublic)
      onArtifactsChange([...artifacts, newArtifact])
      setUploadProgress(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        if (err.status === 429) {
          setUploadError('Upload rate limit reached (maximum 10 uploads per hour). Please wait before uploading again.')
        } else {
          setUploadError(err.message || 'Artifact upload failed. Please try again.')
        }
      } else {
        setUploadError('Artifact upload failed due to a network error. Please try again.')
      }
    } finally {
      setIsUploading(false)
      setUploadProgress(null)
    }
  }

  const handleDelete = async (artifactId: string) => {
    if (!isDraft) return
    try {
      setDeletingId(artifactId)
      setUploadError(null)
      await projectApi.deleteArtifact(artifactId)
      onArtifactsChange(artifacts.filter((a) => a.id !== artifactId))
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setUploadError(err.message || 'Failed to delete artifact.')
      } else {
        setUploadError('Failed to delete artifact.')
      }
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="space-y-4">
      {/* Quota Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-text-muted">
        <div className="flex items-center gap-1.5 font-medium text-text-secondary">
          <HardDrive className="h-4 w-4 text-accent-violet" aria-hidden="true" />
          <span>Deliverable Artifacts Storage</span>
        </div>
        <div className="font-mono">
          {artifacts.length}/{MAX_ARTIFACTS_COUNT} files &bull; {aggregateMb} MB / 50 MB ({aggregatePct}%)
        </div>
      </div>

      {/* Aggregate Storage Progress Bar */}
      <div
        className="h-1.5 w-full overflow-hidden rounded-full bg-bg-surface"
        role="progressbar"
        aria-valuenow={aggregatePct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Storage quota usage"
      >
        <div
          className={`h-full transition-all duration-300 ${
            aggregatePct > 90
              ? 'bg-state-error'
              : aggregatePct > 70
              ? 'bg-state-warning'
              : 'bg-accent-violet'
          }`}
          style={{ width: `${aggregatePct}%` }}
        />
      </div>

      {/* Validation or Upload Error Alert */}
      {validationError && (
        <div
          role="alert"
          className="flex items-start gap-2.5 rounded-lg border border-state-warning/30 bg-state-warning/10 p-3 text-xs text-state-warning"
        >
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" aria-hidden="true" />
          <div className="flex-1 leading-relaxed">
            <strong>Validation Warning:</strong> {validationError}
          </div>
        </div>
      )}

      {uploadError && (
        <div
          role="alert"
          className="flex items-start gap-2.5 rounded-lg border border-state-error/30 bg-state-error/10 p-3 text-xs text-state-error"
        >
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" aria-hidden="true" />
          <div className="flex-1 leading-relaxed">
            <strong>Upload Error:</strong> {uploadError}
          </div>
        </div>
      )}

      {/* Upload Zone (Draft only) */}
      {isDraft && (
        <div className="rounded-xl border border-dashed border-border-medium bg-bg-surface/30 p-5 transition-colors hover:border-accent-violet/50 hover:bg-bg-surface/50 text-center">
          <input
            ref={fileInputRef}
            type="file"
            id="artifact-file-input"
            onChange={handleFileSelect}
            disabled={isUploading || artifacts.length >= MAX_ARTIFACTS_COUNT}
            className="sr-only"
            aria-label="Upload deliverable file"
          />

          <div className="flex flex-col items-center justify-center gap-2">
            <div className="rounded-full bg-accent-violet/10 p-3 text-accent-violet">
              {isUploading ? (
                <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
              ) : (
                <Upload className="h-5 w-5" aria-hidden="true" />
              )}
            </div>

            <div>
              <label
                htmlFor="artifact-file-input"
                className={`inline-block font-semibold text-sm cursor-pointer rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet ${
                  isUploading || artifacts.length >= MAX_ARTIFACTS_COUNT
                    ? 'text-text-muted cursor-not-allowed'
                    : 'text-accent-cyan hover:text-accent-cyan-hover underline underline-offset-4'
                }`}
              >
                {isUploading ? uploadProgress || 'Uploading...' : 'Choose deliverable file to upload'}
              </label>
              <p className="mt-1 text-xs text-text-muted">
                Permitted formats: ZIP, TAR.GZ, PDF, PNG, JPG, WEBP, TXT, MD, JSON, CSV (Max 20 MB/file)
              </p>
            </div>

            {/* Public Showcase Toggle */}
            <div className="mt-2 flex items-center gap-2">
              <input
                type="checkbox"
                id="is-public-artifact"
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
                disabled={isUploading}
                className="h-3.5 w-3.5 rounded border-border-medium bg-bg-base text-accent-violet focus:ring-accent-violet cursor-pointer"
              />
              <label
                htmlFor="is-public-artifact"
                className="text-xs text-text-secondary cursor-pointer select-none flex items-center gap-1"
              >
                <Eye className="h-3 w-3 text-text-muted" aria-hidden="true" />
                <span>Allow showcase in public portfolio (when project is completed)</span>
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Artifacts List */}
      {artifacts.length > 0 ? (
        <div className="rounded-xl border border-border-subtle bg-bg-surface/40 overflow-hidden">
          <ul className="divide-y divide-border-subtle" aria-label="Uploaded Deliverables">
            {artifacts.map((artifact) => {
              const isDeleting = deletingId === artifact.id
              return (
                <li
                  key={artifact.id}
                  className="flex items-center justify-between gap-3 p-3.5 hover:bg-bg-surface/80 transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="rounded-lg bg-bg-elevated p-2 border border-border-subtle shrink-0">
                      {getFileIcon(artifact.original_filename)}
                    </div>

                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-text-primary truncate">
                          {artifact.original_filename}
                        </span>
                        {artifact.is_public ? (
                          <span
                            className="inline-flex items-center gap-1 rounded bg-accent-cyan/10 px-1.5 py-0.5 text-[10px] font-medium text-accent-cyan border border-accent-cyan/20"
                            title="Eligible for public portfolio showcase"
                          >
                            <Eye className="h-2.5 w-2.5" aria-hidden="true" />
                            Showcase
                          </span>
                        ) : (
                          <span
                            className="inline-flex items-center gap-1 rounded bg-bg-elevated px-1.5 py-0.5 text-[10px] text-text-muted border border-border-subtle"
                            title="Private submission deliverable"
                          >
                            <Lock className="h-2.5 w-2.5" aria-hidden="true" />
                            Private
                          </span>
                        )}
                      </div>

                      <div className="mt-0.5 flex items-center gap-2 text-xs text-text-muted font-mono">
                        <span>{formatFileSize(artifact.file_size_bytes)}</span>
                        <span>&bull;</span>
                        <span>{new Date(artifact.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>

                  {/* Actions: Download & Delete */}
                  <div className="flex items-center gap-2 shrink-0">
                    <a
                      href={artifact.download_url}
                      download={artifact.original_filename}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 rounded-md border border-border-subtle bg-bg-surface px-2.5 py-1 text-xs font-medium text-text-secondary hover:bg-bg-elevated hover:text-text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-violet cursor-pointer"
                      aria-label={`Download ${artifact.original_filename}`}
                    >
                      <Download className="h-3.5 w-3.5" aria-hidden="true" />
                      <span className="hidden sm:inline">Download</span>
                    </a>

                    {isDraft && (
                      <button
                        type="button"
                        onClick={() => handleDelete(artifact.id)}
                        disabled={isDeleting}
                        className="inline-flex items-center gap-1 rounded-md border border-border-subtle bg-bg-surface px-2.5 py-1 text-xs font-medium text-state-error/80 hover:bg-state-error/10 hover:text-state-error transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-state-error cursor-pointer disabled:opacity-50"
                        aria-label={`Delete ${artifact.original_filename}`}
                      >
                        {isDeleting ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                        ) : (
                          <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                        )}
                        <span className="hidden sm:inline">Delete</span>
                      </button>
                    )}
                  </div>
                </li>
              )
            })}
          </ul>
        </div>
      ) : (
        <div className="rounded-lg border border-border-subtle bg-bg-surface/20 p-4 text-center text-xs text-text-muted">
          No artifacts attached yet. {isDraft && 'Upload deliverables such as archives, reports, or documentation.'}
        </div>
      )}
    </div>
  )
}
