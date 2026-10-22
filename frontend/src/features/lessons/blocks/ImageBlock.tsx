import React, { useState } from 'react'
import { Image as ImageIcon, AlertCircle } from 'lucide-react'
import type { ImageBlockContent } from '../../../types/lesson'

interface ImageBlockProps {
  content: ImageBlockContent
}

export const ImageBlock: React.FC<ImageBlockProps> = ({ content }) => {
  const [loadError, setLoadError] = useState(false)
  const url = content.url || ''
  const altText = content.alt_text || 'Educational diagram'
  const caption = content.caption

  // Ensure safe URL protocol
  const isSafeUrl = url.startsWith('http://') || url.startsWith('https://') || url.startsWith('/')

  if (!isSafeUrl || loadError) {
    return (
      <figure className="my-6 p-6 rounded-xl border border-border-medium bg-bg-surface text-center space-y-2">
        <div className="w-10 h-10 rounded-full bg-state-error/10 text-state-error mx-auto flex items-center justify-center">
          <AlertCircle className="w-5 h-5" />
        </div>
        <p className="text-xs text-text-muted">
          Unable to display media asset ({altText})
        </p>
        {caption && <figcaption className="text-xs text-text-muted italic">{caption}</figcaption>}
      </figure>
    )
  }

  return (
    <figure className="my-6 space-y-2">
      <div className="relative overflow-hidden rounded-xl border border-border-medium bg-bg-surface flex items-center justify-center">
        <img
          src={url}
          alt={altText}
          loading="lazy"
          onError={() => setLoadError(true)}
          className="w-full max-h-[500px] object-contain rounded-xl transition-opacity duration-300"
        />
      </div>
      {caption && (
        <figcaption className="text-xs text-center text-text-muted font-mono flex items-center justify-center gap-1.5 pt-1">
          <ImageIcon className="w-3.5 h-3.5 text-text-muted/60" />
          <span>{caption}</span>
        </figcaption>
      )}
    </figure>
  )
}
