import React from 'react'
import type { ActivityDetail } from '../../types/activity'
import { SingleChoiceActivity } from './SingleChoiceActivity'
import { MultipleSelectActivity } from './MultipleSelectActivity'
import { TrueFalseActivity } from './TrueFalseActivity'
import { ShortAnswerActivity } from './ShortAnswerActivity'
import { FillBlankActivity } from './FillBlankActivity'
import { OrderingActivity } from './OrderingActivity'
import { MatchingActivity } from './MatchingActivity'
import { ScenarioActivity } from './ScenarioActivity'
import { CodingActivity } from './CodingActivity'

interface ActivityRendererProps {
  activity: ActivityDetail
  submissionState: Record<string, any>
  onSubmissionChange: (updatedState: Record<string, any>) => void
  disabled?: boolean
}

export const ActivityRenderer: React.FC<ActivityRendererProps> = ({
  activity,
  submissionState,
  onSubmissionChange,
  disabled = false,
}) => {
  const config = activity.configuration || {}

  switch (activity.activity_type) {
    case 'single_choice':
      return (
        <SingleChoiceActivity
          options={config.options || []}
          selectedOptionId={submissionState.selected_option_id || null}
          onChange={(optId) => onSubmissionChange({ selected_option_id: optId })}
          disabled={disabled}
        />
      )

    case 'multiple_select':
      return (
        <MultipleSelectActivity
          options={config.options || []}
          selectedOptionIds={submissionState.selected_option_ids || []}
          onChange={(optIds) => onSubmissionChange({ selected_option_ids: optIds })}
          disabled={disabled}
        />
      )

    case 'true_false':
      return (
        <TrueFalseActivity
          statement={config.statement}
          selectedValue={
            typeof submissionState.selected_boolean === 'boolean'
              ? submissionState.selected_boolean
              : null
          }
          onChange={(val) => onSubmissionChange({ selected_boolean: val })}
          disabled={disabled}
        />
      )

    case 'short_answer':
      return (
        <ShortAnswerActivity
          prompt={config.prompt}
          placeholder={config.placeholder}
          maxLength={config.max_length}
          value={submissionState.text || ''}
          onChange={(text) => onSubmissionChange({ text })}
          disabled={disabled}
        />
      )

    case 'fill_in_the_blank':
      return (
        <FillBlankActivity
          template={config.template}
          blanks={config.blanks || []}
          values={submissionState.answers || {}}
          onChange={(bId, val) =>
            onSubmissionChange({
              answers: { ...(submissionState.answers || {}), [bId]: val },
            })
          }
          disabled={disabled}
        />
      )

    case 'ordering': {
      const items = config.items || []
      const currentOrder =
        submissionState.ordered_item_ids && submissionState.ordered_item_ids.length > 0
          ? submissionState.ordered_item_ids
          : items.map((i: any) => i.id)

      return (
        <OrderingActivity
          items={items}
          orderedItemIds={currentOrder}
          onChange={(newOrder) => onSubmissionChange({ ordered_item_ids: newOrder })}
          disabled={disabled}
        />
      )
    }

    case 'matching':
      return (
        <MatchingActivity
          leftItems={config.left_items || []}
          rightItems={config.right_items || []}
          pairs={submissionState.pairs || {}}
          onChange={(lId, rId) =>
            onSubmissionChange({
              pairs: { ...(submissionState.pairs || {}), [lId]: rId },
            })
          }
          disabled={disabled}
        />
      )

    case 'scenario':
      return (
        <ScenarioActivity
          scenarioText={config.scenario_text}
          decisions={config.decisions || []}
          selectedDecisionId={submissionState.selected_decision_id || null}
          onChange={(dId) => onSubmissionChange({ selected_decision_id: dId })}
          disabled={disabled}
        />
      )

    case 'code_exercise':
      return (
        <CodingActivity
          language={config.language}
          taskDescription={config.task_description}
          starterCode={config.starter_code}
          code={
            typeof submissionState.code === 'string'
              ? submissionState.code
              : config.starter_code || ''
          }
          onChange={(code) => onSubmissionChange({ code, language: config.language })}
          disabled={disabled}
        />
      )

    default:
      return (
        <div className="p-4 rounded-xl bg-bg-surface border border-border-subtle text-text-muted text-sm">
          Unsupported activity type: {activity.activity_type}
        </div>
      )
  }
}
