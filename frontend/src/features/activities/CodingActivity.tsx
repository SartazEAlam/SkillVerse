import React from 'react'
import { Code2, Terminal } from 'lucide-react'

interface CodingActivityProps {
  language?: string
  taskDescription?: string
  starterCode?: string
  code: string
  onChange: (code: string) => void
  disabled?: boolean
}

export const CodingActivity: React.FC<CodingActivityProps> = ({
  language = 'javascript',
  taskDescription,
  code = '',
  onChange,
  disabled = false,
}) => {
  return (
    <div className="space-y-4 my-4">
      {taskDescription && (
        <div className="p-4 rounded-xl bg-bg-surface border border-border-medium text-sm text-text-primary leading-relaxed">
          <div className="text-xs font-mono font-bold uppercase tracking-wider text-accent-cyan mb-1.5 flex items-center gap-1.5">
            <Code2 className="w-3.5 h-3.5" />
            <span>Coding Task</span>
          </div>
          <p>{taskDescription}</p>
        </div>
      )}

      <div className="rounded-xl border border-border-medium bg-bg-elevated overflow-hidden shadow-lg">
        {/* Editor Header Bar */}
        <div className="flex items-center justify-between px-4 py-2.5 bg-bg-surface/90 border-b border-border-subtle text-xs font-mono">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5" aria-hidden="true">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500/80 inline-block" />
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80 inline-block" />
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80 inline-block" />
            </div>
            <span className="text-text-muted ml-2">solution.{language === 'python' ? 'py' : 'js'}</span>
          </div>

          <span className="px-2 py-0.5 rounded bg-accent-violet/10 text-accent-violet font-semibold uppercase text-[10px] tracking-wider border border-accent-violet/20">
            {language}
          </span>
        </div>

        {/* Code Input Area */}
        <div className="relative">
          <textarea
            aria-label="Code Editor"
            value={code}
            disabled={disabled}
            onChange={(e) => onChange(e.target.value)}
            spellCheck={false}
            rows={10}
            className="w-full p-4 font-mono text-xs sm:text-sm bg-bg-elevated text-emerald-300 placeholder:text-text-muted focus:outline-none leading-relaxed resize-y border-0 disabled:opacity-70 disabled:cursor-not-allowed selection:bg-accent-violet/30"
          />
        </div>

        <div className="px-4 py-2 bg-bg-surface/50 border-t border-border-subtle/60 flex items-center justify-between text-[11px] font-mono text-text-muted">
          <span className="flex items-center gap-1">
            <Terminal className="w-3 h-3 text-accent-cyan" />
            Isolated Sandbox Environment
          </span>
          <span>{code.split('\n').length} lines</span>
        </div>
      </div>
    </div>
  )
}
