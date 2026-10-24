import React from 'react'
import type { ApiLessonBlock } from '../../types/catalog'
import type {
  HeadingBlockContent,
  TextBlockContent,
  ListBlockContent,
  CodeExampleBlockContent,
  CalloutBlockContent,
  ImageBlockContent,
  VideoBlockContent,
  ActivityBlockContent,
} from '../../types/lesson'
import { HeadingBlock } from './blocks/HeadingBlock'
import { TextBlock } from './blocks/TextBlock'
import { ListBlock } from './blocks/ListBlock'
import { CodeExampleBlock } from './blocks/CodeExampleBlock'
import { CalloutBlock } from './blocks/CalloutBlock'
import { ImageBlock } from './blocks/ImageBlock'
import { VideoBlock } from './blocks/VideoBlock'
import { ActivityBlock } from './blocks/ActivityBlock'
import { UnknownBlock } from './blocks/UnknownBlock'

interface LessonRendererProps {
  blocks: ApiLessonBlock[]
}

export const LessonRenderer: React.FC<LessonRendererProps> = ({ blocks = [] }) => {
  if (!blocks || blocks.length === 0) {
    return (
      <div className="py-12 text-center text-text-muted text-sm border border-dashed border-border-subtle rounded-xl my-6">
        This lesson has no content blocks published yet.
      </div>
    )
  }

  // Sort blocks deterministically by sort_order
  const sortedBlocks = [...blocks].sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))

  return (
    <div className="lesson-content space-y-1">
      {sortedBlocks.map((block) => {
        try {
          switch (block.block_type) {
            case 'heading':
              return (
                <HeadingBlock
                  key={block.id}
                  content={block.content as unknown as HeadingBlockContent}
                />
              )
            case 'text':
              return (
                <TextBlock
                  key={block.id}
                  content={block.content as unknown as TextBlockContent}
                />
              )
            case 'list':
              return (
                <ListBlock
                  key={block.id}
                  content={block.content as unknown as ListBlockContent}
                />
              )
            case 'code_example':
              return (
                <CodeExampleBlock
                  key={block.id}
                  content={block.content as unknown as CodeExampleBlockContent}
                />
              )
            case 'callout':
              return (
                <CalloutBlock
                  key={block.id}
                  content={block.content as unknown as CalloutBlockContent}
                />
              )
            case 'image':
              return (
                <ImageBlock
                  key={block.id}
                  content={block.content as unknown as ImageBlockContent}
                />
              )
            case 'video':
              return (
                <VideoBlock
                  key={block.id}
                  content={block.content as unknown as VideoBlockContent}
                />
              )
            case 'activity':
              return (
                <ActivityBlock
                  key={block.id}
                  content={block.content as unknown as ActivityBlockContent}
                />
              )
            default:
              return (
                <UnknownBlock
                  key={block.id}
                  blockType={block.block_type}
                  blockId={block.id}
                />
              )
          }
        } catch {
          return (
            <UnknownBlock
              key={block.id}
              blockType={block.block_type}
              blockId={block.id}
            />
          )
        }
      })}
    </div>
  )
}
