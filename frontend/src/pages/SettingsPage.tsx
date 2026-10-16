import { Settings, Sun, Moon, Laptop, Palette, Shield, User as UserIcon } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Avatar } from '@/components/ui/Avatar'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme, type Theme } from '@/contexts/ThemeContext'
import { cn } from '@/lib/utils'

export function SettingsPage() {
  const { user } = useAuth()
  const { theme, setTheme } = useTheme()

  const themeOptions: { value: Theme; label: string; description: string; icon: typeof Sun }[] = [
    {
      value: 'light',
      label: 'Light Mode',
      description: 'Crisp slate canvas with clean contrast',
      icon: Sun,
    },
    {
      value: 'dark',
      label: 'Dark Mode',
      description: 'Deep obsidian and slate with luminous accents',
      icon: Moon,
    },
    {
      value: 'system',
      label: 'System Default',
      description: 'Automatically match your OS appearance',
      icon: Laptop,
    },
  ]

  return (
    <div className="flex-1 overflow-y-auto bg-[var(--bg-base)] transition-colors duration-200">
      <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">
        <div>
          <h1 className="text-2xl font-bold mb-1 flex items-center gap-2.5 text-[var(--text-primary)]">
            <Settings className="h-6 w-6 text-[var(--accent-indigo)]" />
            Settings
          </h1>
          <p className="text-sm text-[var(--text-secondary)]">Manage your appearance, profile, and security preferences.</p>
        </div>

        {/* Appearance / Theme */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Palette className="h-4.5 w-4.5 text-[var(--accent-indigo)]" />
              Appearance & Theme
            </CardTitle>
            <CardDescription>Customize how HYPERREALM looks on your device</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {themeOptions.map((opt) => {
                const Icon = opt.icon
                const isSelected = theme === opt.value
                return (
                  <button
                    key={opt.value}
                    onClick={() => setTheme(opt.value)}
                    className={cn(
                      'flex flex-col text-left p-4 rounded-xl border transition-all duration-200 cursor-pointer',
                      isSelected
                        ? 'border-[var(--accent-indigo)] bg-indigo-500/10 shadow-[var(--shadow-sm)] ring-1 ring-[var(--accent-indigo)]'
                        : 'border-[var(--border-default)] bg-[var(--bg-elevated)] hover:border-[var(--border-strong)] hover:bg-[var(--bg-surface)]'
                    )}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div
                        className={cn(
                          'p-2 rounded-lg',
                          isSelected
                            ? 'bg-[var(--accent-indigo)] text-white'
                            : 'bg-[var(--bg-surface)] text-[var(--text-secondary)]'
                        )}
                      >
                        <Icon className="h-5 w-5" />
                      </div>
                      {isSelected && (
                        <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-[var(--accent-indigo)] text-white">
                          Active
                        </span>
                      )}
                    </div>
                    <span className="text-sm font-semibold text-[var(--text-primary)] mb-1">
                      {opt.label}
                    </span>
                    <span className="text-xs text-[var(--text-secondary)] leading-relaxed">
                      {opt.description}
                    </span>
                  </button>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* Profile */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserIcon className="h-4.5 w-4.5 text-[var(--accent-indigo)]" />
              Profile Details
            </CardTitle>
            <CardDescription>Your personal information and role assignments</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              <Avatar name={user?.name ?? ''} size="xl" statusDot="online" />
              <div>
                <p className="text-sm font-semibold text-[var(--text-primary)]">{user?.name ?? 'User'}</p>
                <p className="text-xs text-[var(--text-secondary)] capitalize">{user?.role?.replace(/_/g, ' ')}</p>
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input id="settings-name" label="Full Name" defaultValue={user?.name} />
              <Input id="settings-email" label="Email" type="email" defaultValue={user?.email} />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input id="settings-dept" label="Department" defaultValue={user?.department_name || user?.department || 'Engineering'} />
              <Input id="settings-role" label="Role" defaultValue={user?.role?.replace(/_/g, ' ')} readOnly />
            </div>
            <div className="flex justify-end pt-2">
              <Button size="sm">Save Changes</Button>
            </div>
          </CardContent>
        </Card>

        {/* Security */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-4.5 w-4.5 text-[var(--accent-indigo)]" />
              Security
            </CardTitle>
            <CardDescription>Password and authentication settings</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input id="settings-current-pw" label="Current Password" type="password" placeholder="••••••••" />
            <Input id="settings-new-pw" label="New Password" type="password" placeholder="••••••••" />
            <div className="flex justify-end pt-2">
              <Button size="sm">Update Password</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
