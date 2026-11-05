import React, { useState } from 'react'
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
  const [liveAnnouncement, setLiveAnnouncement] = useState<string>('')

  // Map ordered IDs to actual item objects
  const orderedItems = orderedItemIds.map(
    (id) => items.find((item) => item.id === id) || { id, text: id }
  )

  const moveItem = (index: number, direction: 'up' | 'down' | 'first' | 'last') => {
    if (disabled) return
    let targetIndex = index
    if (direction === 'up') targetIndex = index - 1
    else if (direction === 'down') targetIndex = index + 1
    else if (direction === 'first') targetIndex = 0
    else if (direction === 'last') targetIndex = orderedItemIds.length - 1

    if (targetIndex < 0 || targetIndex >= orderedItemIds.length || targetIndex === index) {
      return
    }

    const newOrder = [...orderedItemIds]
    const [movedId] = newOrder.splice(index, 1)
    newOrder.splice(targetIndex, 0, movedId)

    const itemObj = items.find((it) => it.id === movedId)
    const itemLabel = itemObj ? itemObj.text : movedId
    setLiveAnnouncement(
      `Moved "${itemLabel}" to position ${targetIndex + 1} of ${orderedItemIds.length}`
    )

    onChange(newOrder)
  }

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    if (disabled) return
    if (e.key === 'ArrowUp' || e.key === 'k') {
      e.preventDefault()
      moveItem(index, 'up')
    } else if (e.key === 'ArrowDown' || e.key === 'j') {
      e.preventDefault()
      moveItem(index, 'down')
    } else if (e.key === 'Home') {
      e.preventDefault()
      moveItem(index, 'first')
    } else if (e.key === 'End') {
      e.preventDefault()
      moveItem(index, 'last')
    }
  }

  return (
    <div className="space-y-3 my-4 font-sans">
      <div className="text-xs font-mono uppercase tracking-wider text-text-muted flex items-center justify-between">
        <span>Arrange items in the correct sequence:</span>
        <span className="text-[11px] text-text-muted font-mono">
          Use buttons or focus &amp; Arrow keys
        </span>
      </div>

      {/* Screen reader live region */}
      <div
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
        role="status"
      >
        {liveAnnouncement}
      </div>

      <div
        role="list"
        aria-label="Orderable items list"
        className="space-y-2.5"
      >
        {orderedItems.map((item, index) => {
          const isFirst = index === 0
          const isLast = index === orderedItems.length - 1

          return (
            <div
              key={item.id}
              role="listitem"
              tabIndex={disabled ? -1 : 0}
              onKeyDown={(e) => handleKeyDown(e, index)}
              aria-label={`Position ${index + 1} of ${orderedItems.length}: ${item.text}. Press Up or Down arrow to reorder.`}
              aria-roledescription="sortable item"
              className="flex items-center gap-3 p-3.5 rounded-xl bg-bg-surface border border-border-subtle hover:border-border-medium focus:border-accent-violet focus:ring-1 focus:ring-accent-violet focus:outline-none transition-all"
            >
              <div className="flex items-center gap-1.5 text-text-muted">
                <GripVertical
                  className="w-4 h-4 text-text-muted/60 shrink-0"
                  aria-hidden="true"
                />
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
                  className="p-1.5 rounded-md text-text-secondary hover:text-text-primary hover:bg-bg-elevated disabled:opacity-30 disabled:cursor-not-allowed focus:outline-none focus:ring-1 focus:ring-accent-violet transition-all cursor-pointer"
                >
                  <ArrowUp className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  aria-label={`Move ${item.text} down`}
                  disabled={disabled || isLast}
                  onClick={() => moveItem(index, 'down')}
                  className="p-1.5 rounded-md text-text-secondary hover:text-text-primary hover:bg-bg-elevated disabled:opacity-30 disabled:cursor-not-allowed focus:outline-none focus:ring-1 focus:ring-accent-violet transition-all cursor-pointer"
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
