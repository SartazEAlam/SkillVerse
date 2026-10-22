import React from 'react'
import { Video, ExternalLink, FileText, Clock } from 'lucide-react'
import type { VideoBlockContent } from '../../../types/lesson'

interface VideoBlockProps {
  content: VideoBlockContent
}

function parseEmbedUrl(url: string): string | null {
  try {
    const parsed = new URL(url)
    const hostname = parsed.hostname.toLowerCase()

    // YouTube
    if (hostname.includes('youtube.com') || hostname.includes('youtu.be')) {
      let videoId = ''
      if (hostname.includes('youtu.be')) {
        videoId = parsed.pathname.slice(1)
      } else {
        videoId = parsed.searchParams.get('v') || ''
      }
      if (videoId) {
        return `https://www.youtube-nocookie.com/embed/${encodeURIComponent(videoId)}`
      }
    }

    // Vimeo
    if (hostname.includes('vimeo.com')) {
      const match = parsed.pathname.match(/\/(\d+)/)
      if (match && match[1]) {
        return `https://player.vimeo.com/video/${match[1]}`
      }
    }

    return null
  } catch {
    return null
  }
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  if (mins > 0) {
    return `${mins}m ${secs > 0 ? `${secs}s` : ''}`
  }
  return `${secs}s`
}

export const VideoBlock: React.FC<VideoBlockProps> = ({ content }) => {
  const url = content.url || ''
  const title = content.title || 'Educational Video'
  const duration = content.duration_seconds
  const transcriptUrl = content.transcript_url

  const embedUrl = parseEmbedUrl(url)

  return (
    <div className="my-6 space-y-3">
      {/* Video Embed or Fallback Card */}
      {embedUrl ? (
        <div className="relative aspect-video w-full overflow-hidden rounded-xl border border-border-medium bg-black shadow-lg">
          <iframe
            src={embedUrl}
            title={title}
            loading="lazy"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            sandbox="allow-scripts allow-same-origin allow-presentation"
            className="absolute inset-0 h-full w-full border-0"
          />
        </div>
      ) : (
        <div className="p-6 rounded-xl border border-border-medium bg-bg-surface flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-accent-violet/10 text-accent-violet flex items-center justify-center shrink-0">
              <Video className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-text-primary">{title}</h4>
              <p className="text-xs text-text-muted">External video stream or walkthrough</p>
            </div>
          </div>
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-bg-elevated hover:bg-bg-elevated/80 border border-border-medium text-text-primary transition-colors focus-visible:ring-1 focus-visible:ring-accent-violet"
          >
            <span>Watch Video</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      )}

      {/* Video Details & Meta */}
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-text-muted px-1">
        <span className="font-medium text-text-secondary">{title}</span>

        <div className="flex items-center gap-4">
          {duration && (
            <span className="flex items-center gap-1 font-mono text-[11px]">
              <Clock className="w-3 h-3 text-text-muted" />
              <span>{formatDuration(duration)}</span>
            </span>
          )}

          {transcriptUrl && (
            <a
              href={transcriptUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-accent-cyan hover:underline text-[11px] font-mono"
            >
              <FileText className="w-3 h-3" />
              <span>Transcript</span>
            </a>
          )}
        </div>
      </div>
    </div>
  )
}
