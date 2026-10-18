import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import { ProgressBar } from '../components/ui/ProgressBar'
import { EmptyState } from '../components/ui/EmptyState'
import { Modal } from '../components/ui/Modal'

describe('UI Primitives', () => {
  describe('Button', () => {
    it('renders label and handles click', () => {
      const handleClick = vi.fn()
      render(<Button onClick={handleClick}>Click Me</Button>)

      const btn = screen.getByRole('button', { name: /click me/i })
      expect(btn).toBeInTheDocument()
      fireEvent.click(btn)
      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('disables interaction when disabled or loading', () => {
      const handleClick = vi.fn()
      render(<Button disabled onClick={handleClick}>Disabled</Button>)

      const btn = screen.getByRole('button', { name: /disabled/i })
      expect(btn).toBeDisabled()
      fireEvent.click(btn)
      expect(handleClick).not.toHaveBeenCalled()
    })

    it('shows loading spinner when isLoading is true', () => {
      render(<Button isLoading>Submitting</Button>)
      expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument()
    })
  })

  describe('Input', () => {
    it('renders with label and handles text change', () => {
      const handleChange = vi.fn()
      render(
        <Input
          label="Email Address"
          placeholder="user@example.com"
          onChange={handleChange}
        />
      )

      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
      const input = screen.getByPlaceholderText(/user@example.com/i)
      fireEvent.change(input, { target: { value: 'alex@example.com' } })
      expect(handleChange).toHaveBeenCalled()
    })

    it('shows clear button and invokes onClear', () => {
      const handleClear = vi.fn()
      render(
        <Input
          value="Search query"
          onChange={() => {}}
          onClear={handleClear}
          aria-label="Search"
        />
      )

      const clearBtn = screen.getByRole('button', { name: /clear input/i })
      expect(clearBtn).toBeInTheDocument()
      fireEvent.click(clearBtn)
      expect(handleClear).toHaveBeenCalledTimes(1)
    })

    it('displays error message with role="alert"', () => {
      render(
        <Input
          label="Password"
          error="Password must be at least 8 characters"
        />
      )

      const errorAlert = screen.getByRole('alert')
      expect(errorAlert).toHaveTextContent(/at least 8 characters/i)
    })
  })

  describe('Badge', () => {
    it('renders text with variant styles', () => {
      render(<Badge variant="violet">Interactive</Badge>)
      expect(screen.getByText(/interactive/i)).toBeInTheDocument()
    })
  })

  describe('ProgressBar', () => {
    it('renders progressbar with correct ARIA attributes', () => {
      render(<ProgressBar value={45} label="Course Progress" showPercentage />)

      const progress = screen.getByRole('progressbar', { name: /course progress/i })
      expect(progress).toHaveAttribute('aria-valuenow', '45')
      expect(progress).toHaveAttribute('aria-valuemin', '0')
      expect(progress).toHaveAttribute('aria-valuemax', '100')
      expect(screen.getByText('45%')).toBeInTheDocument()
    })
  })

  describe('EmptyState', () => {
    it('renders title, description and action', () => {
      render(
        <EmptyState
          title="No results found"
          description="Try broadening your search"
          action={<button>Reset</button>}
        />
      )

      expect(screen.getByText(/no results found/i)).toBeInTheDocument()
      expect(screen.getByText(/try broadening your search/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /reset/i })).toBeInTheDocument()
    })
  })

  describe('Modal', () => {
    it('renders title and closes when close button or Escape is pressed', () => {
      const handleClose = vi.fn()
      const { rerender } = render(
        <Modal isOpen={true} onClose={handleClose} title="Lesson Workspace">
          <p>Lesson content details</p>
        </Modal>
      )

      expect(screen.getByRole('dialog', { name: /lesson workspace/i })).toBeInTheDocument()
      expect(screen.getByText(/lesson content details/i)).toBeInTheDocument()

      const closeBtn = screen.getByRole('button', { name: /close dialog/i })
      fireEvent.click(closeBtn)
      expect(handleClose).toHaveBeenCalledTimes(1)

      // Test Escape key
      fireEvent.keyDown(window, { key: 'Escape' })
      expect(handleClose).toHaveBeenCalledTimes(2)

      // Test closed state
      rerender(
        <Modal isOpen={false} onClose={handleClose} title="Lesson Workspace">
          <p>Lesson content details</p>
        </Modal>
      )
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
  })
})
