import React from 'react'
import type { ActivityBlockContent } from '../../../types/lesson'
import { ActivityContainer } from '../../activities/ActivityContainer'

interface ActivityBlockProps {
  content: ActivityBlockContent
}

export const ActivityBlock: React.FC<ActivityBlockProps> = ({ content }) => {
  if (!content || !content.activity_id) {
    return (
      <div className="p-4 rounded-xl border border-dashed border-border-subtle text-text-muted text-xs my-4">
        Missing activity reference.
      </div>
    )
  }

  return (
    <ActivityContainer
      activityId={content.activity_id}
      titleOverride={content.title}
      instructionsOverride={content.instructions}
    />
  )
}
