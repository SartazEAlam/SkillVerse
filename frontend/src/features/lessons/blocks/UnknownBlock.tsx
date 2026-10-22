import React from 'react'
import { HelpCircle } from 'lucide-react'

interface UnknownBlockProps {
  blockType: string
  blockId?: string
}

export const UnknownBlock: React.FC<UnknownBlockProps> = ({ blockType, blockId }) => {
  return (
    <div
      role="status"
      className="my-4 p-4 rounded-xl border border-dashed border-border-medium bg-bg-surface/50 text-xs text-text-muted flex items-start gap-3"
    >
      <HelpCircle className="w-4 h-4 text-text-muted shrink-0 mt-0.5" />
      <div>
        <p className="font-semibold text-text-secondary">Unsupported Content Block</p>
        <p className="mt-0.5 text-[11px]">
          Block type <code className="font-mono text-accent-violet">"{blockType}"</code> ({blockId || 'unknown id'}) is not supported by the current lesson renderer version.
        </p>
      </div>
    </div>
  )
}
