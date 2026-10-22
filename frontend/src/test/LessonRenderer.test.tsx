import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { LessonRenderer } from '../features/lessons/LessonRenderer'
import type { ApiLessonBlock } from '../types/catalog'

describe('LessonRenderer and Content Block Components', () => {
  it('renders heading blocks with semantic h2, h3, and h4 elements', () => {
    const blocks: ApiLessonBlock[] = [
      {
        id: 'h2-blk',
        block_type: 'heading',
        content: { level: 2, text: 'Heading Level Two' },
        sort_order: 1,
      },
      {
        id: 'h3-blk',
        block_type: 'heading',
        content: { level: 3, text: 'Heading Level Three' },
        sort_order: 2,
      },
      {
        id: 'h4-blk',
        block_type: 'heading',
        content: { level: 4, text: 'Heading Level Four' },
        sort_order: 3,
      },
    ]

    render(<LessonRenderer blocks={blocks} />)

    const h2 = screen.getByRole('heading', { level: 2, name: /heading level two/i })
    const h3 = screen.getByRole('heading', { level: 3, name: /heading level three/i })
    const h4 = screen.getByRole('heading', { level: 4, name: /heading level four/i })

    expect(h2).toBeInTheDocument()
    expect(h3).toBeInTheDocument()
    expect(h4).toBeInTheDocument()
  })

  it('renders text block with markdown formatting and sanitizes malicious scripts', () => {
    const blocks: ApiLessonBlock[] = [
      {
        id: 'txt-1',
        block_type: 'text',
        content: {
          format: 'markdown',
          text: 'Welcome to **SkillVerse**. Here is an `inline_code()` sample and <script>alert("xss")</script> safe text.',
        },
        sort_order: 1,
      },
    ]

    render(<LessonRenderer blocks={blocks} />)

    expect(screen.getByText('SkillVerse')).toBeInTheDocument()
    expect(screen.getByText('inline_code()')).toBeInTheDocument()
    // Malicious script must be completely stripped
    expect(screen.queryByText(/alert\("xss"\)/i)).not.toBeInTheDocument()
  })

  it('renders ordered and unordered list blocks properly', () => {
    const blocks: ApiLessonBlock[] = [
      {
        id: 'ul-1',
        block_type: 'list',
        content: {
          ordered: false,
          items: ['First item', 'Second item'],
        },
        sort_order: 1,
      },
      {
        id: 'ol-1',
        block_type: 'list',
        content: {
          ordered: true,
          items: ['Step A', 'Step B'],
        },
        sort_order: 2,
      },
    ]

    render(<LessonRenderer blocks={blocks} />)

    const lists = screen.getAllByRole('list')
    expect(lists).toHaveLength(2)
    expect(screen.getByText('First item')).toBeInTheDocument()
    expect(screen.getByText('Step A')).toBeInTheDocument()
  })

  it('renders code example block with language, caption, and working copy button', async () => {
    // Mock navigator.clipboard
    const writeTextMock = vi.fn().mockResolvedValue(undefined)
    Object.assign(navigator, {
      clipboard: {
        writeText: writeTextMock,
      },
    })

    const blocks: ApiLessonBlock[] = [
      {
        id: 'code-1',
        block_type: 'code_example',
        content: {
          language: 'javascript',
          code: 'const greeting = "Hello SkillVerse";\nconsole.log(greeting);',
          caption: 'Listing 1.1: Greeting script',
          show_line_numbers: true,
        },
        sort_order: 1,
      },
    ]

    render(<LessonRenderer blocks={blocks} />)

    expect(screen.getByText(/javascript/i)).toBeInTheDocument()
    expect(screen.getByText(/Listing 1.1: Greeting script/i)).toBeInTheDocument()
    expect(screen.getByText(/const/i)).toBeInTheDocument()
    expect(screen.getByText(/"Hello SkillVerse"/i)).toBeInTheDocument()

    // Test copy button
    const copyBtn = screen.getByRole('button', { name: /copy code to clipboard/i })
    expect(copyBtn).toBeInTheDocument()

    fireEvent.click(copyBtn)
    expect(writeTextMock).toHaveBeenCalledWith(
      'const greeting = "Hello SkillVerse";\nconsole.log(greeting);'
    )

    // Button updates with feedback
    expect(await screen.findByText(/copied!/i)).toBeInTheDocument()
  })

  it('renders callout blocks with correct variants and icons', () => {
    const blocks: ApiLessonBlock[] = [
      {
        id: 'call-1',
        block_type: 'callout',
        content: {
          variant: 'key_concept',
          title: 'Core Mental Model',
          text: 'State flows down, events bubble up.',
        },
        sort_order: 1,
      },
      {
        id: 'call-2',
        block_type: 'callout',
        content: {
          variant: 'tip',
          title: 'Speed Tip',
          text: 'Use keyboard navigation for speed.',
        },
        sort_order: 2,
      },
    ]

    render(<LessonRenderer blocks={blocks} />)

    expect(screen.getByText('Core Mental Model')).toBeInTheDocument()
    expect(screen.getByText('State flows down, events bubble up.')).toBeInTheDocument()
    expect(screen.getByText('Speed Tip')).toBeInTheDocument()
    expect(screen.getByText('Use keyboard navigation for speed.')).toBeInTheDocument()
  })

  it('renders image blocks with alt text and caption', () => {
    const blocks: ApiLessonBlock[] = [
      {
        id: 'img-1',
        block_type: 'image',
        content: {
          url: 'https://assets.skillverse.dev/diagram.png',
          alt_text: 'System architecture diagram',
          caption: 'Figure 1: Client Server Data Flow',
        },
        sort_order: 1,
      },
    ]

    render(<LessonRenderer blocks={blocks} />)

    const img = screen.getByRole('img', { name: /system architecture diagram/i })
    expect(img).toBeInTheDocument()
    expect(img).toHaveAttribute('src', 'https://assets.skillverse.dev/diagram.png')
    expect(screen.getByText(/Figure 1: Client Server Data Flow/i)).toBeInTheDocument()
  })

  it('renders video blocks with title, duration, and transcript', () => {
    const blocks: ApiLessonBlock[] = [
      {
        id: 'vid-1',
        block_type: 'video',
        content: {
          url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
          title: 'HTTP Protocol Deep Dive',
          duration_seconds: 360,
          transcript_url: 'https://assets.skillverse.dev/transcript.txt',
        },
        sort_order: 1,
      },
    ]

    render(<LessonRenderer blocks={blocks} />)

    expect(screen.getByTitle(/HTTP Protocol Deep Dive/i)).toBeInTheDocument()
    expect(screen.getByText('6m')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /transcript/i })).toHaveAttribute(
      'href',
      'https://assets.skillverse.dev/transcript.txt'
    )
  })

  it('handles unknown or malformed block types gracefully without crashing', () => {
    const blocks: ApiLessonBlock[] = [
      {
        id: 'unknown-1',
        block_type: 'future_ai_simulation' as any,
        content: { foo: 'bar' },
        sort_order: 1,
      },
    ]

    render(<LessonRenderer blocks={blocks} />)

    expect(screen.getByText(/unsupported content block/i)).toBeInTheDocument()
    expect(screen.getByText(/"future_ai_simulation"/i)).toBeInTheDocument()
  })

  it('sorts blocks deterministically according to sort_order', () => {
    const blocks: ApiLessonBlock[] = [
      {
        id: 'b-3',
        block_type: 'heading',
        content: { level: 2, text: 'Third In Order' },
        sort_order: 3,
      },
      {
        id: 'b-1',
        block_type: 'heading',
        content: { level: 2, text: 'First In Order' },
        sort_order: 1,
      },
      {
        id: 'b-2',
        block_type: 'heading',
        content: { level: 2, text: 'Second In Order' },
        sort_order: 2,
      },
    ]

    render(<LessonRenderer blocks={blocks} />)

    const headings = screen.getAllByRole('heading', { level: 2 })
    expect(headings[0]).toHaveTextContent('First In Order')
    expect(headings[1]).toHaveTextContent('Second In Order')
    expect(headings[2]).toHaveTextContent('Third In Order')
  })

  it('renders friendly placeholder when block list is empty', () => {
    render(<LessonRenderer blocks={[]} />)
    expect(screen.getByText(/this lesson has no content blocks published yet/i)).toBeInTheDocument()
  })

  it('neutralizes malicious markdown links with javascript: protocols', () => {
    const blocks: ApiLessonBlock[] = [
      {
        id: 'malicious-link',
        block_type: 'text',
        content: {
          format: 'markdown',
          text: 'Click here for [Dangerous Action](javascript:stealTokens()) safely.',
        },
        sort_order: 1,
      },
    ]

    render(<LessonRenderer blocks={blocks} />)

    const link = screen.getByRole('link', { name: /dangerous action/i })
    expect(link).toHaveAttribute('href', '#')
  })

  it('rejects unsafe image URLs with error fallback placeholder', () => {
    const blocks: ApiLessonBlock[] = [
      {
        id: 'malicious-img',
        block_type: 'image',
        content: {
          url: 'javascript:alert(document.cookie)',
          alt_text: 'Exploit attempt image',
        },
        sort_order: 1,
      },
    ]

    render(<LessonRenderer blocks={blocks} />)

    expect(screen.queryByRole('img')).toBeNull()
    expect(screen.getByText(/unable to display media asset/i)).toBeInTheDocument()
  })

  it('handles clipboard writeText rejection gracefully in code example block', async () => {
    // Mock navigator.clipboard failure
    const writeTextFail = vi.fn().mockRejectedValue(new Error('Permission denied'))
    Object.assign(navigator, {
      clipboard: {
        writeText: writeTextFail,
      },
    })

    const blocks: ApiLessonBlock[] = [
      {
        id: 'code-fail',
        block_type: 'code_example',
        content: {
          language: 'python',
          code: 'print("Protected")',
        },
        sort_order: 1,
      },
    ]

    render(<LessonRenderer blocks={blocks} />)

    const copyBtn = screen.getByRole('button', { name: /copy code to clipboard/i })
    fireEvent.click(copyBtn)

    expect(writeTextFail).toHaveBeenCalled()
    // Should NOT show "Copied!" when clipboard rejects
    expect(screen.queryByText(/copied!/i)).toBeNull()
    expect(screen.getByText(/copy/i)).toBeInTheDocument()
  })
})
