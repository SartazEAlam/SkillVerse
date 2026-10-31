import React, { useState, useEffect, useRef } from 'react'
import {
  X,
  Send,
  Sparkles,
  Bot,
  User as UserIcon,
  AlertCircle,
  HelpCircle,
  RefreshCw,
  Lightbulb,
} from 'lucide-react'
import type { ApiLessonDetail } from '../../types/catalog'
import type { ChatMessage } from '../../types/ai'
import { aiApi } from '../../services/aiApi'
import { Button } from '../../components/ui/Button'

interface AITutorDrawerProps {
  isOpen: boolean
  onClose: () => void
  lesson: ApiLessonDetail | null
}

const DEFAULT_SUGGESTIONS = [
  'Can you explain the main goal of this lesson?',
  'Give me a concrete real-world example',
  'What are the key terms I should understand?',
  'How should I approach the interactive checkpoint?',
]

export const AITutorDrawer: React.FC<AITutorDrawerProps> = ({ isOpen, onClose, lesson }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isOptedOut, setIsOptedOut] = useState(false)
  const [activeProvider, setActiveProvider] = useState<string>('ai')

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Scroll to bottom whenever messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView?.({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        inputRef.current?.focus()
      }, 150)
    }
  }, [isOpen])

  // Reset conversation when lesson changes
  useEffect(() => {
    if (lesson) {
      setMessages([])
      setErrorMessage(null)
      setIsOptedOut(false)
    }
  }, [lesson?.id])

  if (!isOpen) return null

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputMessage).trim()
    if (!text || !lesson || isLoading) return

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)
    setErrorMessage(null)

    try {
      // Build history for context
      const history = messages.slice(-6).map((m) => ({
        role: m.role,
        content: m.content,
      }))

      const res = await aiApi.askTutor({
        lesson_id: lesson.id,
        message: text,
        conversation_history: history,
      })

      setActiveProvider(res.provider)

      const assistantMessage: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: res.reply || res.response || '',
        suggestions: res.suggestions,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (err: any) {
      if (err?.code === 'AI_FEATURE_OPTED_OUT' || err?.status === 403) {
        setIsOptedOut(true)
        setErrorMessage('AI tutoring is currently turned off in your profile preferences.')
      } else if (err?.code === 'RATE_LIMIT_EXCEEDED' || err?.status === 429) {
        setErrorMessage('You have reached the hourly question limit (30/hr). Take a moment to reflect and practice!')
      } else {
        setErrorMessage(err?.message || 'Unable to connect to AI Tutor. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="AI Tutor Assistant"
      className="fixed inset-y-0 right-0 z-50 w-full sm:w-[420px] md:w-[480px] bg-bg-surface border-l border-border-medium shadow-2xl flex flex-col transition-transform duration-300 ease-in-out animate-slideLeft"
    >
      {/* Header */}
      <div className="h-16 px-5 border-b border-border-subtle bg-bg-elevated flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-accent-violet/15 text-accent-violet flex items-center justify-center">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-text-primary">SkillVerse AI Tutor</h2>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-accent-violet/10 text-accent-violet uppercase">
                {activeProvider}
              </span>
            </div>
            <p className="text-[11px] text-text-muted truncate max-w-[220px]">
              {lesson ? lesson.title : 'Pedagogical Guide'}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={onClose}
          aria-label="Close AI Tutor"
          className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-surface transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Notice Banner if Opted Out */}
      {isOptedOut && (
        <div className="p-3 bg-state-warning/10 border-b border-state-warning/20 text-state-warning text-xs flex items-center gap-2 shrink-0">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>AI Tutoring is opted out in your profile preferences. Enable it to chat with the tutor.</span>
        </div>
      )}

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4">
        {/* Welcome Empty State */}
        {messages.length === 0 && (
          <div className="py-6 space-y-4 text-center">
            <div className="w-12 h-12 mx-auto rounded-full bg-accent-violet/10 text-accent-violet flex items-center justify-center">
              <Bot className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-text-primary">
                Pedagogical Lesson Companion
              </h3>
              <p className="text-xs text-text-secondary max-w-xs mx-auto leading-relaxed">
                I am grounded strictly in <strong>{lesson?.title || 'this lesson'}</strong>. Ask for clarifications, mental models, or conceptual breakdowns.
              </p>
            </div>

            {/* Prompt Starter Chips */}
            <div className="pt-2 text-left space-y-2">
              <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider flex items-center gap-1.5">
                <Lightbulb className="w-3.5 h-3.5 text-accent-cyan" />
                <span>Suggested Questions</span>
              </span>
              <div className="flex flex-col gap-1.5">
                {DEFAULT_SUGGESTIONS.map((sug, idx) => (
                  <button
                    key={idx}
                    type="button"
                    disabled={isOptedOut || isLoading}
                    onClick={() => handleSendMessage(sug)}
                    className="p-2.5 rounded-lg text-left text-xs bg-bg-base hover:bg-bg-elevated border border-border-subtle hover:border-accent-violet/30 text-text-secondary hover:text-text-primary transition-colors cursor-pointer flex items-center justify-between gap-2"
                  >
                    <span>{sug}</span>
                    <Sparkles className="w-3 h-3 text-accent-violet/60 shrink-0" />
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Message History */}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div className="flex items-center gap-1.5 mb-1 px-1">
              {msg.role === 'assistant' ? (
                <>
                  <Bot className="w-3 h-3 text-accent-violet" />
                  <span className="text-[10px] font-semibold text-text-muted">AI Tutor</span>
                </>
              ) : (
                <>
                  <span className="text-[10px] font-semibold text-text-muted">You</span>
                  <UserIcon className="w-3 h-3 text-text-muted" />
                </>
              )}
              <span className="text-[9px] text-text-muted/60">{msg.timestamp}</span>
            </div>

            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-xs sm:text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-accent-violet text-white rounded-tr-xs'
                  : 'bg-bg-base border border-border-subtle text-text-primary rounded-tl-xs whitespace-pre-wrap'
              }`}
            >
              {msg.content}
            </div>

            {/* Suggestions Chips from Assistant */}
            {msg.suggestions && msg.suggestions.length > 0 && (
              <div className="mt-2.5 flex flex-wrap gap-1.5 max-w-[85%]">
                {msg.suggestions.map((sug, i) => (
                  <button
                    key={i}
                    type="button"
                    disabled={isOptedOut || isLoading}
                    onClick={() => handleSendMessage(sug)}
                    className="text-[11px] px-2.5 py-1 rounded-full bg-accent-violet/10 text-accent-violet border border-accent-violet/20 hover:bg-accent-violet/20 transition-colors text-left"
                  >
                    {sug}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}

        {/* Typing indicator */}
        {isLoading && (
          <div className="flex items-start gap-2 animate-pulse">
            <div className="w-7 h-7 rounded-full bg-accent-violet/15 text-accent-violet flex items-center justify-center shrink-0">
              <Bot className="w-3.5 h-3.5" />
            </div>
            <div className="bg-bg-base border border-border-subtle rounded-2xl px-4 py-2 text-xs text-text-muted flex items-center gap-1.5">
              <RefreshCw className="w-3 h-3 animate-spin text-accent-violet" />
              <span>Thinking pedagogical response...</span>
            </div>
          </div>
        )}

        {/* Error Message */}
        {errorMessage && (
          <div className="p-3 rounded-xl bg-state-error/10 border border-state-error/30 text-state-error text-xs flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p>{errorMessage}</p>
              {!isOptedOut && (
                <button
                  type="button"
                  onClick={() => handleSendMessage()}
                  className="mt-1 font-semibold underline hover:no-underline cursor-pointer"
                >
                  Retry
                </button>
              )}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form Footer */}
      <div className="p-4 border-t border-border-subtle bg-bg-elevated shrink-0">
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isOptedOut || isLoading}
            placeholder={
              isOptedOut
                ? 'AI Tutor is disabled'
                : 'Ask a question about this lesson...'
            }
            maxLength={1000}
            className="flex-1 bg-bg-surface border border-border-subtle rounded-xl px-3.5 py-2.5 text-xs sm:text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-violet focus:ring-1 focus:ring-accent-violet disabled:opacity-50"
          />

          <Button
            variant="primary"
            size="sm"
            disabled={!inputMessage.trim() || isOptedOut || isLoading}
            onClick={() => handleSendMessage()}
            aria-label="Send message"
            className="shrink-0 rounded-xl px-3"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>

        <div className="mt-2 flex items-center justify-between text-[10px] text-text-muted px-1">
          <span className="flex items-center gap-1">
            <HelpCircle className="w-3 h-3" />
            <span>Answers strictly within lesson context</span>
          </span>
          <span>{inputMessage.length}/1000</span>
        </div>
      </div>
    </div>
  )
}
