import React from 'react'
import { ArrowUp, ArrowDown, GripVertical } from 'lucide-react'
import type { OptionItem } from '../../types/activity'

interface OrderingActivityProps {
  items: OptionItem[]
  orderedItemIds: string[]
  onChange: (orderedIds: string[]) => void
  disabled?: boolean
}

export const OrderingActivity: React.FC<OrderingActivityProps> = ({
  items = [],
  orderedItemIds = [],
  onChange,
  disabled = false,
}) => {
  // Map ordered IDs to actual item objects
  const orderedItems = orderedItemIds.map((id) => items.find((item) => item.id === id) || { id, text: id })

  const moveItem = (index: number, direction: 'up' | 'down') => {
    if (disabled) return
    const targetIndex = direction === 'up' ? index - 1 : index + 1
    if (targetIndex < 0 || targetIndex >= orderedItemIds.length) return

    const newOrder = [...orderedItemIds]
    const temp = newOrder[index]
    newOrder[index] = newOrder[targetIndex]
    newOrder[targetIndex] = temp
    onChange(newOrder)
  }

  return (
    <div className="space-y-3 my-4">
      <div className="text-xs font-mono uppercase tracking-wider text-text-muted flex items-center justify-between">
        <span>Arrange items in the correct sequence:</span>
        <span>Use buttons or keyboard</span>
      </div>

      <div role="list" aria-label="Orderable items list" className="space-y-2.5">
        {orderedItems.map((item, index) => {
          const isFirst = index === 0
          const isLast = index === orderedItems.length - 1

          return (
            <div
              key={item.id}
              role="listitem"
              className="flex items-center gap-3 p-3.5 rounded-xl bg-bg-surface border border-border-subtle hover:border-border-medium transition-all"
            >
              <div className="flex items-center gap-1.5 text-text-muted">
                <GripVertical className="w-4 h-4 text-text-muted/60 shrink-0" aria-hidden="true" />
                <span className="w-6 h-6 rounded-md bg-bg-elevated border border-border-subtle flex items-center justify-center font-mono text-xs font-bold text-accent-violet">
                  {index + 1}
                </span>
              </div>

              <div className="flex-1 text-sm font-medium text-text-primary leading-relaxed">
                {item.text}
              </div>

              <div className="flex items-center gap-1 shrink-0">
                <button
                  type="button"
                  aria-label={`Move ${item.text} up`}
                  disabled={disabled || isFirst}
                  onClick={() => moveItem(index, 'up')}
                  className="p-1.5 rounded-md text-text-secondary hover:text-text-primary hover:bg-bg-elevated disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer"
                >
                  <ArrowUp className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  aria-label={`Move ${item.text} down`}
                  disabled={disabled || isLast}
                  onClick={() => moveItem(index, 'down')}
                  className="p-1.5 rounded-md text-text-secondary hover:text-text-primary hover:bg-bg-elevated disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer"
                >
                  <ArrowDown className="w-4 h-4" />
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
