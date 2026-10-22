import React from 'react'
import type { HeadingBlockContent } from '../../../types/lesson'

interface HeadingBlockProps {
  content: HeadingBlockContent
}

export const HeadingBlock: React.FC<HeadingBlockProps> = ({ content }) => {
  const level = content.level || 2
  const text = content.text || ''

  if (level === 2) {
    return (
      <h2 className="text-xl sm:text-2xl font-bold text-text-primary tracking-tight mt-8 mb-4 border-b border-border-subtle/60 pb-2">
        {text}
      </h2>
    )
  }

  if (level === 3) {
    return (
      <h3 className="text-lg sm:text-xl font-semibold text-text-primary mt-6 mb-3">
        {text}
      </h3>
    )
  }

  return (
    <h4 className="text-base sm:text-lg font-semibold text-text-secondary mt-5 mb-2">
      {text}
    </h4>
  )
}
