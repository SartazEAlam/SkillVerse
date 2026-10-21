import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  User as UserIcon,
  Mail,
  Shield,
  Download,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Settings,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { authApi } from '../services/api'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'

export const ProfilePage: React.FC = () => {
  const navigate = useNavigate()
  const { user, loading, updateProfile, logout } = useAuth()

  // Profile Form States
  const [displayName, setDisplayName] = useState('')
  const [bio, setBio] = useState('')
  const [timezone, setTimezone] = useState('')
  const [avatarUrl, setAvatarUrl] = useState('')

  // Preference States
  const [theme] = useState('dark')
  const [reducedMotion, setReducedMotion] = useState(false)

  // Status & Feedback States
  const [savingProfile, setSavingProfile] = useState(false)
  const [savingPrefs, setSavingPrefs] = useState(false)
  const [downloadingExport, setDownloadingExport] = useState(false)
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  // Delete Account States
  const [deletePassword, setDeletePassword] = useState('')
  const [isDeleting, setIsDeleting] = useState(false)
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)

  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name || '')
      setBio(user.bio || '')
      setTimezone(user.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC')
      setAvatarUrl(user.avatar_url || '')
    }
  }, [user])

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-accent-violet border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!user) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4">
        <div className="max-w-md w-full text-center p-8 bg-bg-surface border border-border-subtle rounded-2xl space-y-4">
          <div className="w-12 h-12 rounded-full bg-accent-violet/20 text-accent-violet mx-auto flex items-center justify-center">
            <UserIcon className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-text-primary">Sign in to view your profile</h2>
          <p className="text-sm text-text-secondary">
            Manage your account settings, UI preferences, and personal progress.
          </p>
          <div className="pt-2 flex justify-center gap-3">
            <Link to="/login">
              <Button variant="primary">Log In</Button>
            </Link>
            <Link to="/register">
              <Button variant="secondary">Register</Button>
            </Link>
          </div>
        </div>
      </div>
    )
  }

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setSavingProfile(true)
      setFeedback(null)
      await updateProfile({
        display_name: displayName,
        bio,
        timezone,
        avatar_url: avatarUrl || undefined,
      })
      setFeedback({ type: 'success', message: 'Profile details saved successfully.' })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to update profile.'
      setFeedback({ type: 'error', message: msg })
    } finally {
      setSavingProfile(false)
    }
  }

  const handleSavePreferences = async () => {
    try {
      setSavingPrefs(true)
      setFeedback(null)
      await authApi.updatePreferences({ theme, reduced_motion: reducedMotion })
      setFeedback({ type: 'success', message: 'Preferences updated successfully.' })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save preferences.'
      setFeedback({ type: 'error', message: msg })
    } finally {
      setSavingPrefs(false)
    }
  }

  const handleExportData = async () => {
    try {
      setDownloadingExport(true)
      const data = await authApi.exportData()
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `skillverse_export_${user.id}_${Date.now()}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      setFeedback({ type: 'success', message: 'Your GDPR data package has been downloaded.' })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Data export failed.'
      setFeedback({ type: 'error', message: msg })
    } finally {
      setDownloadingExport(false)
    }
  }

  const handleDeleteAccount = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!deletePassword) return
    try {
      setIsDeleting(true)
      await authApi.deleteAccount(deletePassword)
      navigate('/login')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete account. Please verify password.'
      setFeedback({ type: 'error', message: msg })
      setIsDeleting(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8 space-y-8">
      {/* Header Profile Summary Banner */}
      <div className="p-6 sm:p-8 rounded-2xl bg-gradient-to-r from-bg-surface via-bg-surface/90 to-bg-elevated border border-border-subtle shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-accent-violet/10 rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 relative z-10">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-accent-violet to-accent-cyan flex items-center justify-center text-white text-xl font-bold shadow-lg">
              {avatarUrl ? (
                <img src={avatarUrl} alt={displayName} className="w-full h-full object-cover rounded-2xl" />
              ) : (
                displayName.charAt(0).toUpperCase() || 'U'
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-bold text-text-primary">
                  {displayName || 'SkillVerse Learner'}
                </h1>
                <Badge variant="cyan" size="sm" className="capitalize">
                  {user.role}
                </Badge>
              </div>
              <p className="text-xs sm:text-sm text-text-secondary flex items-center gap-1.5 mt-0.5">
                <Mail className="w-3.5 h-3.5 text-text-muted" />
                {user.email}
              </p>
              <p className="text-[11px] text-text-muted font-mono mt-1">
                Joined: {new Date(user.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>

          <Button
            type="button"
            variant="secondary"
            onClick={logout}
            className="text-xs border-border-subtle hover:border-state-error/40 hover:text-state-error"
          >
            Sign Out
          </Button>
        </div>
      </div>

      {/* Feedback Banner */}
      {feedback && (
        <div
          role="alert"
          className={`p-4 rounded-xl border flex items-center gap-3 text-sm animate-fadeIn ${
            feedback.type === 'success'
              ? 'bg-state-success/10 border-state-success/30 text-state-success'
              : 'bg-state-error/10 border-state-error/30 text-state-error'
          }`}
        >
          {feedback.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 shrink-0" />
          ) : (
            <AlertCircle className="w-5 h-5 shrink-0" />
          )}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* Section 1: Profile Information */}
      <div className="p-6 rounded-2xl bg-bg-surface border border-border-subtle shadow-sm space-y-6">
        <div className="flex items-center gap-2.5 pb-4 border-b border-border-subtle">
          <UserIcon className="w-5 h-5 text-accent-violet" />
          <div>
            <h2 className="text-base font-semibold text-text-primary">Personal Information</h2>
            <p className="text-xs text-text-secondary">Update your public profile details</p>
          </div>
        </div>

        <form onSubmit={handleSaveProfile} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              id="profile-name"
              label="Display Name"
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              required
            />
            <Input
              id="profile-timezone"
              label="Timezone"
              type="text"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              hint="E.g. UTC, America/New_York, Europe/London"
            />
          </div>

          <Input
            id="profile-avatar"
            label="Avatar Image URL (Optional)"
            type="url"
            placeholder="https://..."
            value={avatarUrl}
            onChange={(e) => setAvatarUrl(e.target.value)}
          />

          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5 uppercase tracking-wider">
              Bio / Learning Objective
            </label>
            <textarea
              rows={3}
              className="w-full bg-bg-inset border border-border-subtle hover:border-border-medium focus:border-transparent focus:ring-2 focus:ring-accent-violet text-text-primary text-sm rounded-lg p-3 transition-colors placeholder:text-text-muted"
              placeholder="Tell others what skills you are learning and what projects you are building..."
              value={bio}
              onChange={(e) => setBio(e.target.value)}
            />
          </div>

          <div className="flex justify-end">
            <Button type="submit" variant="primary" isLoading={savingProfile}>
              Save Profile Details
            </Button>
          </div>
        </form>
      </div>

      {/* Section 2: UI Preferences */}
      <div className="p-6 rounded-2xl bg-bg-surface border border-border-subtle shadow-sm space-y-6">
        <div className="flex items-center gap-2.5 pb-4 border-b border-border-subtle">
          <Settings className="w-5 h-5 text-accent-cyan" />
          <div>
            <h2 className="text-base font-semibold text-text-primary">UI & Experience Preferences</h2>
            <p className="text-xs text-text-secondary">Tailor your learning interface and accessibility</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-3.5 rounded-xl bg-bg-inset border border-border-subtle">
            <div>
              <span className="text-sm font-medium text-text-primary block">Dark First Theme</span>
              <span className="text-xs text-text-muted">High-contrast, sleek dark mode tailored for long study sessions</span>
            </div>
            <Badge variant="cyan" size="sm">Active (Dark)</Badge>
          </div>

          <div className="flex items-center justify-between p-3.5 rounded-xl bg-bg-inset border border-border-subtle">
            <div>
              <span className="text-sm font-medium text-text-primary block">Reduce Motion</span>
              <span className="text-xs text-text-muted">Minimize fluid animations and transitions for accessibility</span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                className="sr-only peer"
                checked={reducedMotion}
                onChange={(e) => setReducedMotion(e.target.checked)}
              />
              <div className="w-11 h-6 bg-border-medium peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent-violet"></div>
            </label>
          </div>

          <div className="flex justify-end">
            <Button type="button" variant="secondary" onClick={handleSavePreferences} isLoading={savingPrefs}>
              Update Preferences
            </Button>
          </div>
        </div>
      </div>

      {/* Section 3: GDPR & Data Portability */}
      <div className="p-6 rounded-2xl bg-bg-surface border border-border-subtle shadow-sm space-y-4">
        <div className="flex items-center gap-2.5 pb-4 border-b border-border-subtle">
          <Shield className="w-5 h-5 text-state-info" />
          <div>
            <h2 className="text-base font-semibold text-text-primary">Privacy & Data Portability (GDPR)</h2>
            <p className="text-xs text-text-secondary">Download a machine-readable archive of all your personal data</p>
          </div>
        </div>

        <p className="text-xs text-text-secondary leading-relaxed">
          In compliance with GDPR and privacy standards, you have the right to request a complete copy of all your profile information, activity metadata, and enrollments in standard JSON format.
        </p>

        <Button
          type="button"
          variant="secondary"
          onClick={handleExportData}
          isLoading={downloadingExport}
          leftIcon={<Download className="w-4 h-4" />}
        >
          Download My Data (JSON)
        </Button>
      </div>

      {/* Section 4: Danger Zone */}
      <div className="p-6 rounded-2xl bg-state-error/5 border border-state-error/20 shadow-sm space-y-4">
        <div className="flex items-center gap-2.5 pb-4 border-b border-state-error/20">
          <Trash2 className="w-5 h-5 text-state-error" />
          <div>
            <h2 className="text-base font-semibold text-state-error">Danger Zone</h2>
            <p className="text-xs text-text-muted">Account deactivation and soft-deletion</p>
          </div>
        </div>

        <p className="text-xs text-text-secondary leading-relaxed">
          Deleting your account initiates a <strong className="text-text-primary">30-day grace period</strong>. You can reactivate your account anytime by logging back in during these 30 days. After 30 days, all account data is permanently erased.
        </p>

        {!deleteModalOpen ? (
          <Button
            type="button"
            variant="destructive"
            onClick={() => setDeleteModalOpen(true)}
            className="text-xs"
          >
            Delete My Account
          </Button>
        ) : (
          <form onSubmit={handleDeleteAccount} className="p-4 rounded-xl bg-bg-inset border border-state-error/30 space-y-3">
            <span className="text-xs font-semibold text-text-primary block">
              Confirm Account Deletion
            </span>
            <Input
              id="confirm-delete-password"
              type="password"
              label="Enter your password to confirm"
              placeholder="••••••••"
              value={deletePassword}
              onChange={(e) => setDeletePassword(e.target.value)}
              required
            />
            <div className="flex gap-2">
              <Button type="submit" variant="destructive" isLoading={isDeleting} disabled={!deletePassword}>
                Permanently Deactivate
              </Button>
              <Button type="button" variant="ghost" onClick={() => setDeleteModalOpen(false)}>
                Cancel
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
