import React from 'react'
import { Link } from 'react-router-dom'
import { LayoutDashboard, Compass, HelpCircle } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'

export const NotFoundPage: React.FC = () => {
  return (
    <div className="py-16 flex items-center justify-center animate-fadeIn">
      <Card variant="elevated" className="max-w-md w-full text-center p-8 space-y-6 border-border-medium shadow-2xl">
        <div className="w-16 h-16 rounded-2xl bg-bg-surface border border-border-subtle mx-auto flex items-center justify-center text-accent-violet">
          <HelpCircle className="w-8 h-8" />
        </div>

        <div>
          <span className="font-mono text-xs uppercase tracking-widest text-accent-violet font-semibold">
            Error 404
          </span>
          <h1 className="text-2xl font-bold text-text-primary mt-1">
            Page Not Found
          </h1>
          <p className="text-sm text-text-secondary mt-2">
            The page or course you are looking for does not exist or may have been relocated.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          <Link to="/" className="w-full sm:w-auto">
            <Button variant="primary" size="md" className="w-full" leftIcon={<LayoutDashboard className="w-4 h-4" />}>
              Dashboard
            </Button>
          </Link>
          <Link to="/explore" className="w-full sm:w-auto">
            <Button variant="outline" size="md" className="w-full" leftIcon={<Compass className="w-4 h-4" />}>
              Explore Courses
            </Button>
          </Link>
        </div>
      </Card>
    </div>
  )
}
