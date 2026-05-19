import { SidebarProvider, Sidebar, SidebarHeader, SidebarContent, SidebarFooter, SidebarGroup, SidebarGroupLabel, SidebarGroupContent, SidebarMenu, SidebarMenuItem, SidebarMenuButton, SidebarTrigger, SidebarInset, SidebarRail } from "@/components/ui/sidebar"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import {
  MessageSquare, LayoutDashboard, FolderOpen, Brain, CheckSquare,
  Bot, Settings, Plus, RefreshCw, Trash2, Globe, User,
  Clock, StopCircle,
} from "lucide-react"
import { toast } from "sonner"
import { cn } from "@/lib/utils"
import { useState, useEffect, useRef } from "react"
import { InputBar } from "@/components/input-bar"
import { ModelPicker, type ModelOption, ProviderConfigDialog, type ProviderConfig } from "@/components/model-picker"
import { AgentPicker } from "@/components/agent-picker"
import { StreamingText, StateIndicator, TypingDots, type StreamState } from "@/components/streaming-text"

type View = "chat" | "dashboard" | "sessions" | "memory" | "tasks" | "agents" | "settings"

interface Message { role: "user" | "custo"; content: string; time: string; streaming?: boolean; state?: StreamState; speed?: number }
interface Session { id: string; title: string; date: string; message_count: number }

const API = window.location.origin

export default function App() {
  const [view, setView] = useState<View>("chat")
  const [messages, setMessages] = useState<Message[]>([{
    role: "custo",
    content: "Hello! I'm **Custo**, your autonomous digital operator.\n\nI can help with coding, research, task management, and more.",
    time: "Just now",
  }])
  const [input, setInput] = useState("")
  const [sending, setSending] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [sessions, setSessions] = useState<Session[]>([])
  const [health, setHealth] = useState<any>(null)
  const [connected, setConnected] = useState(false)
  const [agents, setAgents] = useState<any>(null)
  const [memory, setMemory] = useState<any>(null)
  const [selectedModel, setSelectedModel] = useState("auto")
  const [selectedAgent, setSelectedAgent] = useState("main")
  const [availableModels, setAvailableModels] = useState<ModelOption[]>([
    { id: "auto", name: "Auto", provider: "System", favorite: true },
  ])
  const [modelsLoading, setModelsLoading] = useState(true)
  const [providerConfig, setProviderConfig] = useState<ProviderConfig[]>([])
  const [configOpen, setConfigOpen] = useState(false)
  const [addProviderOpen, setAddProviderOpen] = useState(false)
  const viewportRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => { check(); const i = setInterval(check, 10000); return () => clearInterval(i) }, [])
  useEffect(() => { fetchModels() }, [])
  useEffect(() => {
    const el = viewportRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages])
  useEffect(() => {
    if (view === "dashboard") loadHealth()
    if (view === "sessions") loadSessions()
    if (view === "agents") loadAgents()
    if (view === "memory") loadMemory()
  }, [view])

  // WebSocket connection
  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
    const wsUrl = `${protocol}//${window.location.host}/ws/chat`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onclose = () => {
      setConnected(false)
      // Reconnect after 3 seconds
      setTimeout(() => {
        if (wsRef.current?.readyState !== WebSocket.OPEN) {
          // Trigger re-render to recreate connection
          setConnected(false)
        }
      }, 3000)
    }

    ws.onopen = () => setConnected(true)

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === "state") {
          setMessages(p => {
            const last = p[p.length - 1]
            if (last?.role === "custo" && last.streaming) {
              return [...p.slice(0, -1), { ...last, state: msg.state as StreamState }]
            }
            return p
          })
        } else if (msg.type === "chunk") {
          setMessages(p => {
            const last = p[p.length - 1]
            if (last?.role === "custo" && last.streaming) {
              return [...p.slice(0, -1), { ...last, content: (last.content || "") + msg.text }]
            }
            return p
          })
        } else if (msg.type === "done") {
          setMessages(p => {
            const last = p[p.length - 1]
            if (last?.role === "custo" && last.streaming) {
              if (msg.session_id && !sessionId) setSessionId(msg.session_id)
              return [...p.slice(0, -1), { ...last, streaming: false, state: "done" as StreamState }]
            }
            return p
          })
          setSending(false)
        } else if (msg.type === "error") {
          setMessages(p => {
            const last = p[p.length - 1]
            if (last?.role === "custo" && last.streaming) {
              return [...p.slice(0, -1), { ...last, content: `Error: ${msg.text}`, streaming: false, state: "done" as StreamState }]
            }
            return p
          })
          setSending(false)
        }
      } catch {}
    }

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [])

  async function check() {
    try { const r = await fetch(`${API}/api/health`); if (r.ok) { setConnected(true); setHealth(await r.json()) } else setConnected(false) }
    catch { setConnected(false) }
  }
  async function loadHealth() { try { const r = await fetch(`${API}/api/health`); if (r.ok) setHealth(await r.json()) } catch {} }
  async function loadSessions() { try { const r = await fetch(`${API}/api/sessions`); if (r.ok) { const d = await r.json(); setSessions(d.sessions || []) } } catch {} }
  async function loadAgents() { try { const r = await fetch(`${API}/api/agents`); if (r.ok) setAgents(await r.json()) } catch {} }
  async function loadMemory() { try { const r = await fetch(`${API}/api/memory`); if (r.ok) setMemory(await r.json()) } catch {} }

  async function saveProviderConfig(configs: ProviderConfig[]) {
    setProviderConfig(configs)
    try {
      await fetch(`${API}/api/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider_config: configs }),
      })
    } catch {}
  }

  async function fetchModels() {
    try {
      const res = await fetch("https://models.dev/api.json")
      if (!res.ok) throw new Error("Failed to fetch")
      const data = await res.json()
      const models: ModelOption[] = [{ id: "auto", name: "Auto", provider: "System", favorite: true }]
      const configs: ProviderConfig[] = []

      for (const [providerId, provider] of Object.entries(data)) {
        if (!provider || typeof provider !== "object") continue
        const pDef = provider as any
        const providerName = pDef.name || providerId
        const providerModels = pDef.models || {}

        const providerModelsList: { id: string; name: string; enabled: boolean }[] = []

        if (typeof providerModels === "object") {
          for (const [modelId, mDef] of Object.entries(providerModels)) {
            if (!mDef || typeof mDef !== "object") continue
            const m = mDef as any
            models.push({
              id: modelId,
              name: m.name || modelId,
              provider: providerName,
              version: m.context_length ? `${Math.round(m.context_length / 1024)}K ctx` : undefined,
            })
            providerModelsList.push({ id: modelId, name: m.name || modelId, enabled: false })
          }
        }

        configs.push({ id: providerId, name: providerName, enabled: false, models: providerModelsList })
      }

      setAvailableModels(models)
      setProviderConfig(configs)
      setModelsLoading(false)

      // Load saved config from backend
      try {
        const cfgRes = await fetch(`${API}/api/config`)
        if (cfgRes.ok) {
          const cfg = await cfgRes.json()
          if (cfg.providers && Array.isArray(cfg.providers)) {
            setProviderConfig(cfg.providers)
          }
        }
      } catch {}
    } catch {
      setModelsLoading(false)
    }
  }

  async function send() {
    const t = input.trim(); if (!t || sending) return
    setMessages(p => [...p, { role: "user", content: t, time: ts() }])
    setInput(""); setSending(true)

    // Add streaming assistant message
    const assistantIdx = messages.length + 1
    const baseSpeed = 50 + Math.random() * 20
    setMessages(p => [...p, { role: "custo", content: "", time: ts(), streaming: true, state: "waiting", speed: baseSpeed }])

    // Send via WebSocket
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        message: t,
        session_id: sessionId,
        model_id: selectedModel,
        agent_id: selectedAgent,
      }))
    } else {
      // Fallback to HTTP if WebSocket not connected
      try {
        const payload: any = { message: t, model_id: selectedModel, agent_id: selectedAgent }
        if (sessionId) payload.session_id = sessionId
        const r = await fetch(`${API}/api/chat`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        const d = await r.json(); if (d.session_id && !sessionId) setSessionId(d.session_id)
        setMessages(p => p.map((m, i) => i === assistantIdx ? { ...m, content: d.response || "No response.", streaming: false, state: "done" as StreamState } : m))
        setSending(false)
      } catch (e: any) {
        setMessages(p => p.map((m, i) => i === assistantIdx ? { ...m, content: `Error: ${e.message}`, streaming: false, state: "done" as StreamState } : m))
        setSending(false)
      }
    }
  }

  function ts() { return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) }

  function fmt(c: string) {
    return c.split("\n").map((l, i) => {
      if (l.startsWith("```")) return <pre key={i} className="my-2 rounded-md bg-muted p-3 text-sm overflow-x-auto"><code>{l.replace(/```/g, "")}</code></pre>
      const parts = l.split(/(\*\*[^*]+\*\*|`[^`]+`)/g)
      return <p key={i} className="mb-1 last:mb-0">{parts.map((p, j) => {
        if (p.startsWith("**") && p.endsWith("**")) return <strong key={j}>{p.slice(2, -2)}</strong>
        if (p.startsWith("`") && p.endsWith("`")) return <code key={j} className="rounded bg-muted px-1.5 py-0.5 text-sm">{p.slice(1, -1)}</code>
        return <span key={j}>{p}</span>
      })}</p>
    })
  }

  const mainNav = [
    { id: "chat" as View, label: "Chat", icon: MessageSquare },
    { id: "dashboard" as View, label: "Dashboard", icon: LayoutDashboard },
  ]
  const workNav = [
    { id: "sessions" as View, label: "Sessions", icon: FolderOpen, badge: sessions.length },
    { id: "memory" as View, label: "Memory", icon: Brain },
    { id: "tasks" as View, label: "Tasks", icon: CheckSquare },
  ]
  const sysNav = [
    { id: "agents" as View, label: "Agents", icon: Bot },
    { id: "settings" as View, label: "Settings", icon: Settings },
  ]

  const agentIcons: Record<string, any> = { main: Bot, researcher: MessageSquare, coder: MessageSquare, strategist: LayoutDashboard }

  const activeModels = availableModels.filter((m) => {
    if (m.id === "auto") return true
    const provider = providerConfig.find((p) => p.name === m.provider)
    if (!provider || !provider.enabled) return false
    const model = provider.models.find((mod) => mod.id === m.id)
    return model ? model.enabled : false
  })

  const agentOptions = [
    { id: "main", name: "Main", description: "General purpose" },
    { id: "researcher", name: "Researcher", description: "Deep research" },
    { id: "coder", name: "Coder", description: "Code generation" },
    { id: "strategist", name: "Strategist", description: "Planning" },
  ]

  return (
    <SidebarProvider>
      <Sidebar variant="inset" collapsible="icon">
        <SidebarHeader>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton size="lg">
                <Avatar className="size-8 bg-gradient-to-br from-zinc-400 to-zinc-600">
                  <AvatarFallback><Globe className="size-4 text-white" /></AvatarFallback>
                </Avatar>
                <div className="flex flex-col gap-0.5 leading-none">
                  <span className="font-semibold">Custo</span>
                  <span className="text-xs text-muted-foreground">Autonomous Operator</span>
                </div>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarHeader>
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>Main</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {mainNav.map(n => (
                  <SidebarMenuItem key={n.id}>
                    <SidebarMenuButton isActive={view === n.id} onClick={() => setView(n.id)} tooltip={n.label}>
                      <n.icon className="size-4" /><span>{n.label}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
          <SidebarGroup>
            <SidebarGroupLabel>Workspace</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {workNav.map(n => (
                  <SidebarMenuItem key={n.id}>
                    <SidebarMenuButton isActive={view === n.id} onClick={() => setView(n.id)} tooltip={n.label}>
                      <n.icon className="size-4" /><span>{n.label}</span>
                      {n.badge !== undefined && n.badge > 0 && <Badge variant="secondary" className="ml-auto text-xs">{n.badge}</Badge>}
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
          <SidebarGroup>
            <SidebarGroupLabel>System</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {sysNav.map(n => (
                  <SidebarMenuItem key={n.id}>
                    <SidebarMenuButton isActive={view === n.id} onClick={() => setView(n.id)} tooltip={n.label}>
                      <n.icon className="size-4" /><span>{n.label}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
        <SidebarFooter>
          <div className="flex items-center gap-2 px-2 py-1.5">
            <div className={cn("size-2.5 rounded-full shrink-0", connected ? "bg-emerald-500" : "bg-red-500")} />
            <span className="text-xs text-muted-foreground truncate">{connected ? "Connected" : "Disconnected"}</span>
          </div>
        </SidebarFooter>
        <SidebarRail />
      </Sidebar>

      <SidebarInset className="flex flex-col h-screen overflow-hidden">
        <header className="flex h-12 shrink-0 items-center gap-2 px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="h-4" />
          <h1 className="text-sm font-medium text-muted-foreground capitalize">{view}</h1>
          <div className="ml-auto flex items-center gap-2">
            {view === "chat" && <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={() => { setSessionId(null); setMessages([{ role: "custo", content: "New session started. How can I help?", time: ts() }]); toast.success("New session created") }}><Plus className="mr-1 size-3" />New</Button>}
            {view === "sessions" && <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={loadSessions}><RefreshCw className="mr-1 size-3" />Refresh</Button>}
          </div>
        </header>
        <Separator />

        <main className="flex-1 min-h-0 overflow-hidden">
          {view === "chat" && (
            <div className="flex flex-col h-full">
              <ScrollArea className="flex-1 min-h-0" viewportRef={viewportRef}>
                <div className="mx-auto max-w-3xl px-6 py-4 space-y-6">
                  {messages.map((m, i) => (
                    <div key={i} className={cn("flex gap-3", m.role === "user" && "flex-row-reverse")}>
                      <Avatar className={cn("size-7 shrink-0 mt-0.5", m.role === "custo" ? "bg-gradient-to-br from-zinc-400 to-zinc-600" : "bg-muted")}>
                        <AvatarFallback className="text-xs">{m.role === "custo" ? <Globe className="size-3.5 text-white" /> : <User className="size-3.5" />}</AvatarFallback>
                      </Avatar>
                      <div className={cn("max-w-[80%]", m.role === "user" && "items-end flex flex-col")}>
                        <div className={cn("rounded-lg px-3 py-2 text-sm leading-relaxed", m.role === "custo" ? "bg-card" : "bg-muted")}>
                          {m.role === "custo" && m.streaming ? (
                            <>
                              <StateIndicator state={m.state || "waiting"} />
                              {m.content ? <StreamingText text={m.content} baseSpeed={m.speed || 60} /> : <TypingDots />}
                            </>
                          ) : (
                            fmt(m.content)
                          )}
                        </div>
                        <p className="text-[10px] text-muted-foreground mt-1">{m.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
              <Separator />
              <InputBar
                value={input}
                onChange={setInput}
                onSend={() => send()}
                status={sending ? "streaming" : "ready"}
                placeholder="Message Custo..."
                autoFocus
                onAttach={() => toast.info("File attachment coming soon")}
                leftActions={
                  <>
                    <ModelPicker
                    models={activeModels}
                    value={selectedModel}
                    onChange={setSelectedModel}
                    onAddProvider={() => setAddProviderOpen(true)}
                    onConfigure={() => setConfigOpen(true)}
                  />
                    <AgentPicker agents={agentOptions} value={selectedAgent} onChange={setSelectedAgent} />
                  </>
                }
              />
            </div>
          )}

          {view === "dashboard" && (
            <ScrollArea className="h-full">
              <div className="p-6 space-y-6 max-w-5xl mx-auto">
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                  <Stat label="Sessions Today" value={health?.sessions_today ?? "--"} sub="Active conversations" />
                  <Stat label="Memory Entries" value={health?.memory_entries ?? "--"} sub="Stored knowledge" />
                  <Stat label="Active Tasks" value={health?.active_tasks ?? "--"} sub="In progress" />
                  <Stat label="Uptime" value={health?.uptime ?? "--"} sub={health?.daemon_status ?? "Unknown"} />
                </div>
                <div className="rounded-lg border bg-card">
                  <div className="p-4 border-b"><h3 className="font-medium">System Info</h3></div>
                  <div className="p-4 space-y-2 text-sm">
                    <InfoRow label="Version" value={health?.version || "1.0.0"} />
                    <InfoRow label="Daemon" value={health?.daemon_status || "Unknown"} />
                    <InfoRow label="Provider" value={health?.llm_provider || "Not configured"} />
                    <InfoRow label="Model" value={health?.llm_model || "Not configured"} />
                    <InfoRow label="Port" value={health?.port || "N/A"} />
                  </div>
                </div>
              </div>
            </ScrollArea>
          )}

          {view === "sessions" && (
            <ScrollArea className="h-full">
              <div className="p-6 max-w-3xl mx-auto">
                {sessions.length === 0 ? <Empty icon={FolderOpen} title="No sessions yet" desc="Start a conversation in Chat to create your first session." /> : (
                  <div className="space-y-2">
                    {sessions.map(s => (
                      <div key={s.id} className="flex items-center gap-4 rounded-lg border bg-card p-4 cursor-pointer hover:bg-accent transition-colors group" onClick={() => { setSessionId(s.id); setView("chat"); toast.info(`Resumed ${s.id.slice(0, 8)}`) }}>
                        <Avatar className="size-10 bg-muted"><AvatarFallback><MessageSquare className="size-5 text-muted-foreground" /></AvatarFallback></Avatar>
                        <div className="flex-1 min-w-0"><p className="font-medium truncate">{s.title || "Untitled"}</p><p className="text-sm text-muted-foreground">{s.message_count || 0} messages · {s.date}</p></div>
                        <Button variant="ghost" size="icon" className="opacity-0 group-hover:opacity-100 transition-opacity h-8 w-8" onClick={e => { e.stopPropagation(); fetch(`${API}/api/sessions/${s.id}`, { method: "DELETE" }).then(() => { loadSessions(); toast.success("Deleted") }) }}><Trash2 className="size-4" /></Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </ScrollArea>
          )}

          {view === "memory" && (
            <ScrollArea className="h-full">
              <div className="p-6 max-w-3xl mx-auto">
                {!memory?.inbox || memory.inbox.length === 0 ? <Empty icon={Brain} title="Memory is empty" desc="Start chatting to build knowledge." /> : (
                  <div className="space-y-2">
                    {memory.inbox.map((item: any, i: number) => (
                      <div key={i} className="flex items-center gap-4 rounded-lg border bg-card p-4">
                        <Avatar className="size-10 bg-muted"><AvatarFallback><Brain className="size-5 text-muted-foreground" /></AvatarFallback></Avatar>
                        <div className="flex-1 min-w-0"><p className="font-medium truncate">{item.data?.text || item.id || "Entry"}</p><p className="text-sm text-muted-foreground">{item.created || "Unknown"}</p></div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </ScrollArea>
          )}

          {view === "tasks" && <div className="h-full flex items-center justify-center"><Empty icon={CheckSquare} title="Tasks" desc="Track your tasks and let Custo manage them." /></div>}

          {view === "agents" && (
            <ScrollArea className="h-full">
              <div className="p-6 max-w-3xl mx-auto">
                {!agents?.agents || Object.keys(agents.agents).length === 0 ? <Empty icon={Bot} title="No agents" desc="Run `custo daemon start` to initialize." /> : (
                  <div className="space-y-2">
                    {Object.entries(agents.agents).map(([id, a]: [string, any]) => {
                      const Icon = agentIcons[id] || Bot
                      return (
                        <div key={id} className="flex items-center gap-4 rounded-lg border bg-card p-4">
                          <Avatar className="size-10 bg-muted"><AvatarFallback><Icon className="size-5 text-muted-foreground" /></AvatarFallback></Avatar>
                          <div className="flex-1"><p className="font-medium">{a.name}</p>
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              {a.running ? <><Clock className="size-3.5 text-emerald-500" /><span className="text-emerald-500">Running</span></> : <><StopCircle className="size-3.5" /><span>Stopped</span></>}
                              <span>· PID: {a.pid || "—"}</span><span>· {a.enabled ? "Enabled" : "Disabled"}</span>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            </ScrollArea>
          )}

          {view === "settings" && <div className="h-full flex items-center justify-center"><Empty icon={Settings} title="Settings" desc={<>Edit <code className="rounded bg-muted px-1.5 py-0.5 text-sm">system/config.yaml</code> for advanced options.</>} /></div>}
        </main>
      </SidebarInset>

      <ProviderConfigDialog
        providers={providerConfig}
        open={configOpen}
        onOpenChange={setConfigOpen}
        onChange={saveProviderConfig}
      />
    </SidebarProvider>
  )
}

function Stat({ label, value, sub }: { label: string; value: string | number; sub: string }) {
  return <div className="rounded-lg border bg-card p-5"><p className="text-xs font-medium uppercase tracking-wide text-muted-foreground mb-2">{label}</p><p className="text-3xl font-bold">{value}</p><p className="text-xs text-muted-foreground mt-1">{sub}</p></div>
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return <div className="flex justify-between"><span className="text-muted-foreground">{label}</span><span className="font-medium">{value}</span></div>
}

function Empty({ icon: Icon, title, desc }: { icon: any; title: string; desc: React.ReactNode }) {
  return <div className="flex flex-col items-center justify-center py-20 text-center"><Icon className="size-12 text-muted-foreground/40 mb-4" /><h3 className="text-lg font-medium mb-2">{title}</h3><p className="text-sm text-muted-foreground max-w-md">{desc}</p></div>
}
