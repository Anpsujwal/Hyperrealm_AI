import { Link } from 'react-router-dom'
import {
  BookOpen,
  BarChart2,
  Users,
  GraduationCap,
  ArrowRight,
  Shield,
  Globe,
  Cpu,
  ChevronRight,
  Sun,
  Moon,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { useTheme } from '@/contexts/ThemeContext'

const CURRENT_YEAR = new Date().getFullYear()

// ── Agent card data ──────────────────────────────────────────────────────────
const agents = [
  {
    id: 'knowledge',
    name: 'Knowledge Agent',
    tagline: "Instant access to your org's collective intelligence",
    description:
      'Retrieves, synthesises, and explains internal documentation, wikis, and SOPs via Vertex AI Search.',
    icon: BookOpen,
    color: '#6366f1',
    gradient: 'from-blue-500/10 via-indigo-500/5 to-transparent dark:from-zinc-900 dark:to-zinc-950',
    border: 'border-blue-200/80 dark:border-zinc-800',
    features: ['Document retrieval', 'Semantic search', 'Policy Q&A', 'Version diff'],
  },
  {
    id: 'insights',
    name: 'Insights Agent',
    tagline: 'Data-driven intelligence at conversational speed',
    description:
      'Analyzes operational metrics, incident patterns, and business data to surface actionable intelligence.',
    icon: BarChart2,
    color: '#8b5cf6',
    gradient: 'from-purple-500/10 via-violet-500/5 to-transparent dark:from-zinc-900 dark:to-zinc-950',
    border: 'border-purple-200/80 dark:border-zinc-800',
    features: ['Trend analysis', 'Incident insights', 'KPI tracking', 'Audit reports'],
  },
  {
    id: 'collaborate',
    name: 'Collaborate Agent',
    tagline: 'Smart coordination for high-performance teams',
    description:
      'Manages tasks, schedules stand-ups, coordinates approvals, and keeps distributed teams aligned.',
    icon: Users,
    color: '#22d3ee',
    gradient: 'from-cyan-500/10 via-sky-500/5 to-transparent dark:from-zinc-900 dark:to-zinc-950',
    border: 'border-cyan-200/80 dark:border-zinc-800',
    features: ['Task assignment', 'Meeting summaries', 'Scrum scheduling', 'Approvals'],
  },
  {
    id: 'onboard',
    name: 'Onboard Agent',
    tagline: 'Role-specific guidance from day one',
    description:
      'Delivers personalised learning paths, KT workflows, and guideline versioning for every role.',
    icon: GraduationCap,
    color: '#10b981',
    gradient: 'from-emerald-500/10 via-teal-500/5 to-transparent dark:from-zinc-900 dark:to-zinc-950',
    border: 'border-emerald-200/80 dark:border-zinc-800',
    features: ['Learning paths', 'KT workflows', 'Guideline versioning', 'Role-based'],
  },
]

const stats = [
  { value: '4', label: 'Specialist Agents' },
  { value: '99.9%', label: 'Uptime SLA' },
  { value: 'SOC2', label: 'Certified' },
  { value: '<200ms', label: 'Response P95' },
]

const capabilities = [
  {
    icon: Cpu,
    title: 'Gemini on Vertex AI',
    description: "Powered by Google's most capable enterprise AI, running on your GCP infrastructure.",
  },
  {
    icon: Shield,
    title: 'Enterprise Security',
    description: 'Role-based access control, audit trails, and data residency controls built in.',
  },
  {
    icon: Globe,
    title: 'Unified Orchestration',
    description: 'HYPERREALM routes every query to the right specialist agent automatically.',
  },
]

export function LandingPage() {
  const { resolvedTheme, toggleTheme } = useTheme()

  return (
    <div className="min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)]">
      {/* ── Nav ───────────────────────────────────────────────────────────── */}
      <header className="fixed top-0 left-0 right-0 z-50 h-16 flex items-center px-6 glass border-b border-[var(--border-default)]">
        <Link to="/" className="flex items-center gap-3" aria-label="HYPERREALM home">
          <div className="relative h-9 w-9 rounded-xl overflow-hidden border border-cyan-500/40 shadow-[0_0_16px_rgba(6,182,212,0.35)] flex items-center justify-center bg-zinc-950 flex-shrink-0">
            <img src="/hyperrealm-logo.jpg" alt="HYPERREALM Logo" className="h-full w-full object-cover scale-110" />
          </div>
          <span className="font-display text-base font-bold tracking-tight text-[var(--text-primary)]">HYPERREALM</span>
          <span className="hidden sm:inline-block px-2 py-0.5 text-[9px] font-semibold rounded-full bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-rose-500/10 text-purple-600 dark:text-zinc-300 dark:bg-none dark:bg-zinc-800 border border-purple-500/25 dark:border-zinc-700">
            Gemini Powered
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-7 ml-10 text-xs uppercase tracking-wider font-semibold text-[var(--text-secondary)]">
          <a href="#agents" className="hover:text-[var(--text-primary)] transition-colors">Agents</a>
          <a href="#platform" className="hover:text-[var(--text-primary)] transition-colors">Platform</a>
          <a href="#enterprise" className="hover:text-[var(--text-primary)] transition-colors">Enterprise</a>
        </nav>

        <div className="flex items-center gap-3 ml-auto">
          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            type="button"
            className="p-2 rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
            title={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
            aria-label="Toggle theme"
          >
            {resolvedTheme === 'dark' ? (
              <Sun className="h-4 w-4 text-amber-400" />
            ) : (
              <Moon className="h-4 w-4 text-indigo-500" />
            )}
          </button>

          <Link to="/login">
            <Button variant="ghost" size="sm" className="rounded-full px-4">Sign In</Button>
          </Link>
          <Link to="/signup">
            <Button variant="gemini" size="sm" className="rounded-full px-4">Sign Up</Button>
          </Link>
        </div>
      </header>

      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <section className="relative pt-36 pb-28 px-6 overflow-hidden">
        {/* Gemini Aurora Background — completely hidden in dark mode */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[550px] rounded-full bg-gradient-to-tr from-blue-400/10 via-purple-400/10 to-rose-300/10 dark:hidden blur-[130px] pointer-events-none" />
        <div className="absolute top-28 right-1/4 w-[450px] h-[450px] rounded-full bg-purple-400/8 dark:hidden blur-[110px] pointer-events-none" />

        <div className="relative max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-gradient-to-r from-cyan-500/10 via-purple-500/10 to-rose-500/10 dark:bg-none dark:bg-zinc-800 border border-cyan-500/30 dark:border-zinc-700 text-xs font-semibold text-cyan-600 dark:text-cyan-300 mb-8 shadow-xs dark:shadow-none">
            <div className="h-4 w-4 rounded-full overflow-hidden flex-shrink-0 border border-cyan-400/40">
              <img src="/hyperrealm-logo.jpg" alt="" className="h-full w-full object-cover scale-125" />
            </div>
            <span>AI-Powered Enterprise Intelligence Platform</span>
          </div>

          <h1 className="font-display text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.08] mb-6">
            <span className="text-[var(--text-primary)]">The command center</span>
            <br />
            <span className="text-gemini">for intelligent work</span>
          </h1>

          <p className="text-lg md:text-xl text-[var(--text-secondary)] max-w-2xl mx-auto mb-10 leading-relaxed font-normal">
            HYPERREALM unifies your organisation's collective knowledge, operations, and learning into a
            single AI-orchestrated platform — powered by specialist agents and Google Gemini on Vertex AI.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/signup">
              <Button size="lg" variant="gemini" className="w-full sm:w-auto rounded-full px-8 shadow-xl text-base">
                Start for Free
                <ArrowRight className="h-4.5 w-4.5 ml-1" />
              </Button>
            </Link>
            <Link to="/login">
              <Button variant="secondary" size="lg" className="w-full sm:w-auto rounded-full px-8 text-base">
                Sign In to Workspace
              </Button>
            </Link>
          </div>

          {/* Stats row */}
          <div className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-6 max-w-3xl mx-auto p-6 rounded-2xl border border-[var(--border-default)] dark:border-zinc-800 bg-[var(--bg-surface)]/60 dark:bg-zinc-900/80 backdrop-blur-md">
            {stats.map((s) => (
              <div key={s.label} className="text-center">
                <p className="font-display text-3xl font-bold text-gemini">{s.value}</p>
                <p className="text-xs text-[var(--text-muted)] mt-1 font-medium">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Agents ────────────────────────────────────────────────────────── */}
      <section id="agents" className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <Badge variant="violet" className="mb-4 mx-auto">Four Specialist Agents</Badge>
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              The right expert for every task
            </h2>
            <p className="text-[var(--text-secondary)] max-w-xl mx-auto">
              HYPERREALM automatically selects the most capable agent — or you can choose
              manually for complete control.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-5">
            {agents.map((agent) => {
              const Icon = agent.icon
              return (
                <div
                  key={agent.id}
                  className={`relative rounded-[var(--radius-xl)] border bg-gradient-to-br ${agent.gradient} ${agent.border} p-6 group hover:scale-[1.01] transition-transform duration-300`}
                >
                  <div className="flex items-start gap-4 mb-4">
                    <div
                      className="h-10 w-10 rounded-[var(--radius-md)] flex items-center justify-center flex-shrink-0"
                      style={{ backgroundColor: `${agent.color}20` }}
                    >
                      <Icon className="h-5 w-5" style={{ color: agent.color }} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-[var(--text-primary)]">{agent.name}</h3>
                      <p className="text-xs text-[var(--text-secondary)] mt-0.5">{agent.tagline}</p>
                    </div>
                  </div>

                  <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-5">
                    {agent.description}
                  </p>

                  <div className="flex flex-wrap gap-2">
                    {agent.features.map((f) => (
                      <span
                        key={f}
                        className="text-xs px-2.5 py-1 rounded-full border"
                        style={{
                          color: agent.color,
                          borderColor: `${agent.color}30`,
                          backgroundColor: `${agent.color}10`,
                        }}
                      >
                        {f}
                      </span>
                    ))}
                  </div>

                  <ChevronRight
                    className="absolute bottom-5 right-5 h-4 w-4 opacity-0 group-hover:opacity-60 transition-opacity"
                    style={{ color: agent.color }}
                  />
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* ── Platform capabilities ─────────────────────────────────────────── */}
      <section id="platform" className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <Badge variant="cyan" className="mb-4 mx-auto">Enterprise Platform</Badge>
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Built for mission-critical organisations
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-6" id="enterprise">
            {capabilities.map((cap) => {
              const Icon = cap.icon
              return (
                <div
                  key={cap.title}
                  className="rounded-[var(--radius-xl)] border border-[var(--border-default)] bg-[var(--bg-surface)] p-6 hover:border-[var(--border-strong)] transition-colors"
                >
                  <div className="h-10 w-10 rounded-[var(--radius-md)] bg-indigo-500/15 flex items-center justify-center mb-4">
                    <Icon className="h-5 w-5 text-[var(--accent-indigo)]" />
                  </div>
                  <h3 className="font-semibold mb-2">{cap.title}</h3>
                  <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                    {cap.description}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────────────────────── */}
      <section className="py-24 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <div className="relative rounded-[var(--radius-xl)] border border-indigo-200/70 dark:border-zinc-800 bg-gradient-to-br from-indigo-50/90 via-violet-50/50 to-[var(--bg-surface)] dark:from-zinc-900 dark:to-zinc-950 p-12 overflow-hidden shadow-sm dark:shadow-none">
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(99,102,241,0.08)_0%,transparent_70%)] dark:hidden pointer-events-none" />
            <div className="relative">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">
                Ready to transform your organisation?
              </h2>
              <p className="text-[var(--text-secondary)] mb-8 max-w-lg mx-auto">
                Join forward-thinking enterprises using HYPERREALM to unlock the full
                productivity potential of AI.
              </p>
              <Link to="/signup">
                <Button size="lg" className="glow-indigo dark:shadow-none">
                  Create Your Workspace
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────────────────────── */}
      <footer className="border-t border-[var(--border-default)] dark:border-zinc-800 py-8 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="h-7 w-7 rounded-lg overflow-hidden border border-cyan-500/30 shadow-xs flex items-center justify-center bg-zinc-950 flex-shrink-0">
              <img src="/hyperrealm-logo.jpg" alt="HYPERREALM" className="h-full w-full object-cover scale-110" />
            </div>
            <span className="text-sm font-bold tracking-wide">HYPERREALM</span>
          </div>
          <p className="text-xs text-[var(--text-muted)]">
            © {CURRENT_YEAR} HYPERREALM. Enterprise AI Productivity Platform.
          </p>
          <div className="flex gap-5 text-xs text-[var(--text-muted)]">
            <a href="#" className="hover:text-[var(--text-secondary)] transition-colors">Privacy</a>
            <a href="#" className="hover:text-[var(--text-secondary)] transition-colors">Terms</a>
            <a href="#" className="hover:text-[var(--text-secondary)] transition-colors">Security</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
