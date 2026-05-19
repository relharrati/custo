import React, { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { TooltipProvider } from "@/components/ui/tooltip"
import { Toaster } from "@/components/ui/sonner"
import App from "./App"
import "./index.css"

function ErrorFallback({ error }: { error: Error }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-8">
      <div className="max-w-lg rounded-lg border bg-card p-6 text-card-foreground">
        <h2 className="mb-2 text-lg font-semibold text-destructive">App Error</h2>
        <pre className="overflow-auto rounded bg-muted p-3 text-sm">{error.message}</pre>
        <p className="mt-3 text-sm text-muted-foreground">
          Check the browser console for details.
        </p>
      </div>
    </div>
  )
}

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null }
  static getDerivedStateFromError(error: Error) {
    return { error }
  }
  render() {
    if (this.state.error) return <ErrorFallback error={this.state.error} />
    return this.props.children
  }
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ErrorBoundary>
      <TooltipProvider>
        <App />
        <Toaster />
      </TooltipProvider>
    </ErrorBoundary>
  </StrictMode>
)
