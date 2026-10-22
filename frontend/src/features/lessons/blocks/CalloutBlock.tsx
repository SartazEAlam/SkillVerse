import React from 'react'
import { Sparkles, Info, AlertTriangle, CheckCircle2 } from 'lucide-react'
import type { CalloutBlockContent, CalloutVariant } from '../../../types/lesson'

interface CalloutBlockProps {
  content: CalloutBlockContent
}

interface VariantConfig {
  icon: React.ReactNode
  defaultTitle: string
  containerClasses: string
  titleClasses: string
}

function getVariantConfig(variant: CalloutVariant): VariantConfig {
  switch (variant) {
    case 'key_concept':
      return {
        icon: <Sparkles className="w-4 h-4 text-accent-violet shrink-0 mt-0.5" />,
        defaultTitle: 'Core Concept',
        containerClasses: 'bg-accent-violet/10 border-accent-violet/30 text-text-primary',
        titleClasses: 'text-accent-violet',
      }
    case 'tip':
      return {
        icon: <CheckCircle2 className="w-4 h-4 text-state-success shrink-0 mt-0.5" />,
        defaultTitle: 'Pro Tip',
        containerClasses: 'bg-state-success/10 border-state-success/30 text-text-primary',
        titleClasses: 'text-state-success',
      }
    case 'warning':
      return {
        icon: <AlertTriangle className="w-4 h-4 text-state-warning shrink-0 mt-0.5" />,
        defaultTitle: 'Important Consideration',
        containerClasses: 'bg-state-warning/10 border-state-warning/30 text-text-primary',
        titleClasses: 'text-state-warning',
      }
    case 'info':
    default:
      return {
        icon: <Info className="w-4 h-4 text-accent-cyan shrink-0 mt-0.5" />,
        defaultTitle: 'Note',
        containerClasses: 'bg-accent-cyan/10 border-accent-cyan/30 text-text-primary',
        titleClasses: 'text-accent-cyan',
      }
  }
}

export const CalloutBlock: React.FC<CalloutBlockProps> = ({ content }) => {
  const variant =
    content.variant ||
    (content as unknown as { callout_type?: CalloutVariant }).callout_type ||
    'info'
  const config = getVariantConfig(variant)
  const title = content.title || config.defaultTitle
  const text =
    content.text ||
    (content as unknown as { content?: string }).content ||
    (content as unknown as { message?: string }).message ||
    ''

  return (
    <div
      role="note"
      className={`my-5 p-4 sm:p-5 rounded-xl border flex items-start gap-3.5 transition-colors ${config.containerClasses}`}
    >
      {config.icon}
      <div className="space-y-1 min-w-0 flex-1">
        {title && <h5 className={`text-xs font-bold uppercase tracking-wider ${config.titleClasses}`}>{title}</h5>}
        <p className="text-xs sm:text-sm text-text-secondary leading-relaxed">
          {text}
        </p>
      </div>
    </div>
  )
}
