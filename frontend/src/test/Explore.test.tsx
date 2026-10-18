import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ExplorePage } from '../pages/ExplorePage'

describe('ExplorePage Interaction', () => {
  const renderExplore = () =>
    render(
      <MemoryRouter>
        <ExplorePage />
      </MemoryRouter>
    )

  it('renders all sample courses initially', () => {
    renderExplore()
    expect(screen.getByText(/web development foundations/i)).toBeInTheDocument()
    expect(screen.getByText(/spoken english and professional communication/i)).toBeInTheDocument()
    expect(screen.getByText(/personal productivity and systems thinking/i)).toBeInTheDocument()
    expect(screen.getByText(/showing 5 of 5 courses/i)).toBeInTheDocument()
  })

  it('filters courses by text search query', () => {
    renderExplore()
    const searchInput = screen.getByLabelText(/search courses/i)

    fireEvent.change(searchInput, { target: { value: 'flexbox' } })

    expect(screen.getByText(/web development foundations/i)).toBeInTheDocument()
    expect(screen.queryByText(/spoken english and professional communication/i)).not.toBeInTheDocument()
    expect(screen.getByText(/showing 1 of 5 courses/i)).toBeInTheDocument()
  })

  it('filters courses by category chip', () => {
    renderExplore()
    const commBtn = screen.getByRole('button', { name: /^communication$/i })

    fireEvent.click(commBtn)

    expect(screen.getByText(/spoken english and professional communication/i)).toBeInTheDocument()
    expect(screen.queryByText(/web development foundations/i)).not.toBeInTheDocument()
    expect(screen.getByText(/showing 1 of 5 courses/i)).toBeInTheDocument()
  })

  it('displays empty state when no courses match and allows resetting filters', () => {
    renderExplore()
    const searchInput = screen.getByLabelText(/search courses/i)

    fireEvent.change(searchInput, { target: { value: 'quantum mechanics non-existent course' } })

    expect(screen.getByText(/no matching courses found/i)).toBeInTheDocument()
    expect(screen.getByText(/showing 0 of 5 courses/i)).toBeInTheDocument()

    const resetBtn = screen.getByRole('button', { name: /reset all filters/i })
    fireEvent.click(resetBtn)

    expect(screen.getByText(/web development foundations/i)).toBeInTheDocument()
    expect(screen.getByText(/showing 5 of 5 courses/i)).toBeInTheDocument()
  })
})
