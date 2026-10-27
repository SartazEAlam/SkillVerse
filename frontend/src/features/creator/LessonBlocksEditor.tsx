import React, { useState, useEffect } from 'react'
import {
  Trash2,
  ArrowUp,
  ArrowDown,
  Save,
  Type,
  Heading,
  List,
  Code,
  AlertTriangle,
  Image as ImageIcon,
  Video,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react'
import { creatorApi } from '../../services/creatorApi'
import { Button } from '../../components/ui/Button'

interface BlockItem {
  id: string
  type: string
  data: Record<string, unknown>
}

interface LessonBlocksEditorProps {
  courseId: string
  lessonId: string
  lessonTitle: string
  initialBlocks?: BlockItem[]
  onSaved: () => void
}

const BLOCK_TYPES = [
  { type: 'text', label: 'Narrative Text', icon: Type, desc: 'Markdown narrative paragraph' },
  { type: 'heading', label: 'Section Heading', icon: Heading, desc: 'H2, H3, or H4 section header' },
  { type: 'list', label: 'Bulleted List', icon: List, desc: 'Ordered or bulleted points' },
  { type: 'code_example', label: 'Code Snippet', icon: Code, desc: 'Syntax highlighted code sample' },
  { type: 'callout', label: 'Callout Box', icon: AlertTriangle, desc: 'Tip, warning, or important alert' },
  { type: 'image', label: 'Illustration / Image', icon: ImageIcon, desc: 'Web image with alt text' },
  { type: 'video', label: 'Video Embed', icon: Video, desc: 'Streaming video lecture or demo' },
]

export const LessonBlocksEditor: React.FC<LessonBlocksEditorProps> = ({
  courseId,
  lessonId,
  lessonTitle,
  initialBlocks = [],
  onSaved,
}) => {
  const [blocks, setBlocks] = useState<BlockItem[]>(initialBlocks)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState<boolean>(false)
  const [saving, setSaving] = useState<boolean>(false)
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setBlocks(initialBlocks)
    setHasUnsavedChanges(false)
  }, [lessonId, initialBlocks])

  const updateBlockData = (id: string, newData: Record<string, unknown>) => {
    setBlocks((prev) =>
      prev.map((b) => (b.id === id ? { ...b, data: { ...b.data, ...newData } } : b))
    )
    setHasUnsavedChanges(true)
    setSaveSuccess(false)
  }

  const addBlock = (type: string) => {
    const nextId = `blk-${Math.random().toString(36).slice(2, 9)}`
    let initialData: Record<string, unknown> = {}

    switch (type) {
      case 'heading':
        initialData = { level: 2, text: 'New Section Heading' }
        break
      case 'text':
        initialData = { text: 'Enter narrative text here...' }
        break
      case 'list':
        initialData = { ordered: false, items: ['First key takeaway', 'Second key takeaway'] }
        break
      case 'code_example':
        initialData = { language: 'python', code: '# Code example\nprint("Hello, SkillVerse!")' }
        break
      case 'callout':
        initialData = { variant: 'tip', text: 'Important tip for learners.' }
        break
      case 'image':
        initialData = { url: 'https://images.unsplash.com/photo-1516116211227-bbc8f2e21258', alt: 'Illustration' }
        break
      case 'video':
        initialData = { url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', title: 'Video Lecture' }
        break
      default:
        initialData = { text: '' }
    }

    setBlocks((prev) => [...prev, { id: nextId, type, data: initialData }])
    setHasUnsavedChanges(true)
    setSaveSuccess(false)
  }

  const removeBlock = (id: string) => {
    setBlocks((prev) => prev.filter((b) => b.id !== id))
    setHasUnsavedChanges(true)
    setSaveSuccess(false)
  }

  const moveBlock = (index: number, direction: 'up' | 'down') => {
    const target = direction === 'up' ? index - 1 : index + 1
    if (target < 0 || target >= blocks.length) return
    const updated = [...blocks]
    const [moved] = updated.splice(index, 1)
    updated.splice(target, 0, moved)
    setBlocks(updated)
    setHasUnsavedChanges(true)
    setSaveSuccess(false)
  }

  const handleSaveBlocks = async () => {
    setSaving(true)
    setError(null)
    setSaveSuccess(false)

    try {
      await creatorApi.updateLessonContent(courseId, lessonId, {
        document: {
          schema_version: '1.0',
          blocks: blocks.map((b) => ({
            id: b.id,
            type: b.type,
            data: b.data,
          })),
        },
      })
      setHasUnsavedChanges(false)
      setSaveSuccess(true)
      onSaved()
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e.message || 'Failed to save lesson content blocks.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 bg-slate-900/80 border border-slate-800 rounded-xl">
        <div>
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            Structured Content Blocks
            {hasUnsavedChanges && (
              <span className="text-[11px] font-semibold text-amber-400 bg-amber-950/60 px-2 py-0.5 rounded-full border border-amber-800/50">
                Unsaved changes
              </span>
            )}
            {saveSuccess && !hasUnsavedChanges && (
              <span className="text-[11px] font-semibold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded-full border border-emerald-800/50 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                Saved
              </span>
            )}
          </h3>
          <p className="text-xs text-slate-400">
            Author sequential content modules for &quot;{lessonTitle}&quot;.
          </p>
        </div>

        <Button
          type="button"
          onClick={handleSaveBlocks}
          disabled={saving || !hasUnsavedChanges}
          className="flex items-center gap-2 text-xs"
        >
          <Save className="w-4 h-4" />
          {saving ? 'Saving Blocks...' : 'Save Lesson Blocks'}
        </Button>
      </div>

      {error && (
        <div className="p-3.5 bg-red-950/40 border border-red-800/60 rounded-xl flex items-center gap-2 text-red-200 text-xs">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Blocks sequence */}
      <div className="space-y-4">
        {blocks.map((block, idx) => (
          <div
            key={block.id}
            className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3 transition-all hover:border-slate-700"
          >
            {/* Block meta bar */}
            <div className="flex items-center justify-between pb-2 border-b border-slate-800/60">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold text-indigo-400 uppercase tracking-wider bg-indigo-950/60 px-2 py-0.5 rounded">
                  #{idx + 1} {block.type}
                </span>
              </div>

              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => moveBlock(idx, 'up')}
                  disabled={idx === 0}
                  className="p-1 text-slate-400 hover:text-indigo-400 disabled:opacity-20"
                  title="Move block up"
                >
                  <ArrowUp className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => moveBlock(idx, 'down')}
                  disabled={idx === blocks.length - 1}
                  className="p-1 text-slate-400 hover:text-indigo-400 disabled:opacity-20"
                  title="Move block down"
                >
                  <ArrowDown className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => removeBlock(block.id)}
                  className="p-1 text-slate-400 hover:text-red-400 transition-colors ml-2"
                  title="Delete block"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Block Form Fields by Type */}
            {block.type === 'heading' && (
              <div className="grid grid-cols-4 gap-3">
                <div className="col-span-1">
                  <label className="block text-[11px] text-slate-400 mb-1">Level</label>
                  <select
                    value={String(block.data.level || 2)}
                    onChange={(e) => updateBlockData(block.id, { level: Number(e.target.value) })}
                    className="w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-slate-100"
                  >
                    <option value="2">H2 (Major Topic)</option>
                    <option value="3">H3 (Subtopic)</option>
                    <option value="4">H4 (Sub-section)</option>
                  </select>
                </div>
                <div className="col-span-3">
                  <label className="block text-[11px] text-slate-400 mb-1">Heading Text</label>
                  <input
                    type="text"
                    value={String(block.data.text || '')}
                    onChange={(e) => updateBlockData(block.id, { text: e.target.value })}
                    className="w-full px-3 py-1.5 bg-slate-800 border border-slate-700 rounded text-sm text-slate-100 font-semibold"
                    required
                  />
                </div>
              </div>
            )}

            {block.type === 'text' && (
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Markdown Body</label>
                <textarea
                  rows={4}
                  value={String(block.data.text || '')}
                  onChange={(e) => updateBlockData(block.id, { text: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-xs text-slate-100 font-mono"
                  required
                />
              </div>
            )}

            {block.type === 'list' && (
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">
                  List Items (one per line)
                </label>
                <textarea
                  rows={4}
                  value={((block.data.items as string[]) || []).join('\n')}
                  onChange={(e) =>
                    updateBlockData(block.id, {
                      items: e.target.value
                        .split('\n')
                        .map((s) => s.trim())
                        .filter((s) => s.length > 0),
                    })
                  }
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-xs text-slate-100"
                  required
                />
              </div>
            )}

            {block.type === 'code_example' && (
              <div className="space-y-2">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] text-slate-400 mb-1">Language</label>
                    <input
                      type="text"
                      value={String(block.data.language || 'python')}
                      onChange={(e) => updateBlockData(block.id, { language: e.target.value })}
                      className="w-full px-3 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-slate-100 font-mono"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">Code</label>
                  <textarea
                    rows={5}
                    value={String(block.data.code || '')}
                    onChange={(e) => updateBlockData(block.id, { code: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-xs text-emerald-400 font-mono"
                    spellCheck={false}
                    required
                  />
                </div>
              </div>
            )}

            {block.type === 'callout' && (
              <div className="space-y-2">
                <div className="w-1/3">
                  <label className="block text-[11px] text-slate-400 mb-1">Alert Variant</label>
                  <select
                    value={String(block.data.variant || 'tip')}
                    onChange={(e) => updateBlockData(block.id, { variant: e.target.value })}
                    className="w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-slate-100"
                  >
                    <option value="tip">Tip</option>
                    <option value="info">Info</option>
                    <option value="warning">Warning</option>
                    <option value="important">Important</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">Callout Text</label>
                  <input
                    type="text"
                    value={String(block.data.text || '')}
                    onChange={(e) => updateBlockData(block.id, { text: e.target.value })}
                    className="w-full px-3 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-slate-100"
                    required
                  />
                </div>
              </div>
            )}

            {block.type === 'image' && (
              <div className="space-y-2">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] text-slate-400 mb-1">Image URL</label>
                    <input
                      type="url"
                      value={String(block.data.url || '')}
                      onChange={(e) => updateBlockData(block.id, { url: e.target.value })}
                      placeholder="https://..."
                      className="w-full px-3 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-slate-100 font-mono"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-slate-400 mb-1">Alt Text</label>
                    <input
                      type="text"
                      value={String(block.data.alt || '')}
                      onChange={(e) => updateBlockData(block.id, { alt: e.target.value })}
                      placeholder="Descriptive caption"
                      className="w-full px-3 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-slate-100"
                    />
                  </div>
                </div>
              </div>
            )}

            {block.type === 'video' && (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">Video Stream URL</label>
                  <input
                    type="url"
                    value={String(block.data.url || '')}
                    onChange={(e) => updateBlockData(block.id, { url: e.target.value })}
                    placeholder="https://..."
                    className="w-full px-3 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-slate-100 font-mono"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">Video Title</label>
                  <input
                    type="text"
                    value={String(block.data.title || '')}
                    onChange={(e) => updateBlockData(block.id, { title: e.target.value })}
                    className="w-full px-3 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-slate-100"
                  />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Add block toolbar */}
      <div className="p-4 bg-slate-900/40 border border-slate-800 border-dashed rounded-xl">
        <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
          Insert Content Block
        </label>
        <div className="flex flex-wrap gap-2">
          {BLOCK_TYPES.map((bt) => {
            const Icon = bt.icon
            return (
              <button
                key={bt.type}
                type="button"
                onClick={() => addBlock(bt.type)}
                className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-xs font-medium text-slate-200 transition-colors"
              >
                <Icon className="w-3.5 h-3.5 text-indigo-400" />
                {bt.label}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
