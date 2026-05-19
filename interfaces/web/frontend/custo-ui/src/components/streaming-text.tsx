"use client";

import { useEffect, useRef, useState, memo } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Brain, Search, Code, MessageSquare, Clock } from "lucide-react";

export type StreamState =
  | "idle"
  | "waiting"
  | "thinking"
  | "reasoning"
  | "analyzing"
  | "coding"
  | "searching"
  | "streaming"
  | "done";

const stateConfig: Record<Exclude<StreamState, "idle" | "done">, { label: string; icon: React.ReactNode; color: string }> = {
  waiting: { label: "Waiting", icon: <Clock className="size-3" />, color: "text-muted-foreground" },
  thinking: { label: "Thinking", icon: <Brain className="size-3" />, color: "text-purple-400" },
  reasoning: { label: "Reasoning", icon: <Brain className="size-3" />, color: "text-blue-400" },
  analyzing: { label: "Analyzing", icon: <Search className="size-3" />, color: "text-emerald-400" },
  coding: { label: "Writing code", icon: <Code className="size-3" />, color: "text-amber-400" },
  searching: { label: "Searching", icon: <Search className="size-3" />, color: "text-cyan-400" },
  streaming: { label: "Streaming", icon: <MessageSquare className="size-3" />, color: "text-muted-foreground" },
};

export function StateIndicator({ state }: { state: StreamState }) {
  if (state === "idle" || state === "done") return null;
  const cfg = stateConfig[state];
  return (
    <div className="flex items-center gap-2 px-1 pb-2">
      <div className={cn("animate-pulse", cfg.color)}>{cfg.icon}</div>
      <span className={cn("text-[11px] font-medium", cfg.color)}>
        <ShiningText text={cfg.label} />
      </span>
    </div>
  );
}

export function ShiningText({ text, className }: { text: string; className?: string }) {
  return (
    <motion.span
      className={cn(
        "bg-[linear-gradient(110deg,#6b7280,35%,#e5e7eb,50%,#6b7280,75%,#6b7280)] bg-[length:200%_100%] bg-clip-text text-transparent",
        className
      )}
      initial={{ backgroundPosition: "200% 0" }}
      animate={{ backgroundPosition: "-200% 0" }}
      transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
    >
      {text}
    </motion.span>
  );
}

export function StreamingText({
  text,
  className,
  baseSpeed = 60,
}: {
  text: string;
  className?: string;
  baseSpeed?: number;
}) {
  const [displayed, setDisplayed] = useState("");
  const indexRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const textRef = useRef(text);

  useEffect(() => {
    textRef.current = text;
    indexRef.current = 0;
    setDisplayed("");
  }, [text]);

  useEffect(() => {
    if (indexRef.current >= textRef.current.length) return;

    const typeNext = () => {
      if (indexRef.current >= textRef.current.length) return;

      const char = textRef.current[indexRef.current];
      const isPunctuation = [".", ",", "!", "?", ";", ":"].includes(char);
      const isWhitespace = char === " " || char === "\n";
      
      let delay = baseSpeed + (Math.random() * 20 - 10);
      
      if (isPunctuation) delay += 80;
      else if (isWhitespace) delay += 20;
      
      indexRef.current++;
      setDisplayed(textRef.current.slice(0, indexRef.current));
      
      timerRef.current = setTimeout(typeNext, delay);
    };

    timerRef.current = setTimeout(typeNext, 50);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [text, baseSpeed]);

  return <span className={className}>{displayed}</span>;
}

export function TypingDots() {
  return (
    <div className="flex items-center gap-1 px-1 py-1">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="size-1.5 rounded-full bg-muted-foreground/60"
          animate={{ y: [0, -4, 0], opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.15 }}
        />
      ))}
    </div>
  );
}
