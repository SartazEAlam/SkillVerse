import React from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { Button } from '../../../components/ui/Button'

interface TestCase {
  id: string
  description: string
  input?: string
  expected_output?: string
}

interface CodeExerciseConfigFormProps {
  config: {
    prompt?: string
    language?: string
    starter_code?: string
  }
  answerKey: {
    solution?: string
    test_cases?: TestCase[]
  }
  onChange: (config: Record<string, unknown>, answerKey: Record<string, unknown>) => void
}

const LANGUAGES = [
  { id: 'python', name: 'Python' },
  { id: 'javascript', name: 'JavaScript' },
  { id: 'typescript', name: 'TypeScript' },
  { id: 'sql', name: 'SQL' },
  { id: 'html', name: 'HTML' },
  { id: 'css', name: 'CSS' },
]

export const CodeExerciseConfigForm: React.FC<CodeExerciseConfigFormProps> = ({
  config,
  answerKey,
  onChange,
}) => {
  const prompt = config.prompt || ''
  const language = config.language || 'python'
  const starterCode = config.starter_code || 'def solution():\n    # write code here\n    pass\n'
  const solution = answerKey.solution || 'def solution():\n    return True\n'
  const testCases: TestCase[] = answerKey.test_cases || [
    { id: 'tc-1', description: 'Basic sanity test', expected_output: 'True' },
  ]

  const updateConfig = (key: string, val: unknown) => {
    onChange({ ...config, [key]: val }, answerKey)
  }

  const updateAnswerKey = (key: string, val: unknown) => {
    onChange(config, { ...answerKey, [key]: val })
  }

  const handleTestCaseChange = (index: number, field: keyof TestCase, val: string) => {
    const updated = [...testCases]
    updated[index] = { ...updated[index], [field]: val }
    updateAnswerKey('test_cases', updated)
  }

  const addTestCase = () => {
    const nextId = `tc-${Date.now()}`
    const updated = [...testCases, { id: nextId, description: 'Test case', expected_output: '' }]
    updateAnswerKey('test_cases', updated)
  }

  const removeTestCase = (index: number) => {
    if (testCases.length <= 1) return
    const updated = testCases.filter((_, i) => i !== index)
    updateAnswerKey('test_cases', updated)
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="md:col-span-2">
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
            Problem Prompt *
          </label>
          <input
            type="text"
            value={prompt}
            onChange={(e) => updateConfig('prompt', e.target.value)}
            placeholder="e.g. Implement a function to calculate Fibonacci numbers."
            className="w-full px-3.5 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 text-sm"
            required
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
            Language *
          </label>
          <select
            value={language}
            onChange={(e) => updateConfig('language', e.target.value)}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-indigo-500 text-sm"
          >
            {LANGUAGES.map((l) => (
              <option key={l.id} value={l.id}>
                {l.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
            Starter Code (visible to learner)
          </label>
          <textarea
            rows={5}
            value={starterCode}
            onChange={(e) => updateConfig('starter_code', e.target.value)}
            className="w-full p-3 bg-slate-950 border border-slate-800 rounded-lg text-emerald-400 font-mono text-xs focus:outline-none focus:border-indigo-500"
            spellCheck={false}
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
            Reference Solution (secret / authoring only)
          </label>
          <textarea
            rows={5}
            value={solution}
            onChange={(e) => updateAnswerKey('solution', e.target.value)}
            className="w-full p-3 bg-slate-950 border border-slate-800 rounded-lg text-indigo-400 font-mono text-xs focus:outline-none focus:border-indigo-500"
            spellCheck={false}
          />
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Test Cases *
          </label>
          <span className="text-xs text-slate-500">Configured test suites for sandbox execution</span>
        </div>

        <div className="space-y-2.5">
          {testCases.map((tc, idx) => (
            <div
              key={tc.id}
              className="p-3 bg-slate-900/60 border border-slate-800 rounded-lg space-y-2"
            >
              <div className="flex items-center justify-between">
                <input
                  type="text"
                  value={tc.description}
                  onChange={(e) => handleTestCaseChange(idx, 'description', e.target.value)}
                  placeholder="Test case description"
                  className="px-2 py-1 bg-slate-800 border border-slate-700 rounded text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 w-2/3"
                />
                <button
                  type="button"
                  onClick={() => removeTestCase(idx)}
                  disabled={testCases.length <= 1}
                  className="p-1 text-slate-500 hover:text-red-400 disabled:opacity-30 disabled:pointer-events-none transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <input
                  type="text"
                  value={tc.input || ''}
                  onChange={(e) => handleTestCaseChange(idx, 'input', e.target.value)}
                  placeholder="Input arguments (optional)"
                  className="px-2.5 py-1.5 bg-slate-950 border border-slate-800 rounded text-xs text-slate-200 font-mono placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                />
                <input
                  type="text"
                  value={tc.expected_output || ''}
                  onChange={(e) => handleTestCaseChange(idx, 'expected_output', e.target.value)}
                  placeholder="Expected stdout / return value"
                  className="px-2.5 py-1.5 bg-slate-950 border border-slate-800 rounded text-xs text-slate-200 font-mono placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>
          ))}
        </div>

        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={addTestCase}
          className="mt-3 text-xs"
        >
          <Plus className="w-3.5 h-3.5 mr-1" />
          Add Test Case
        </Button>
      </div>
    </div>
  )
}
