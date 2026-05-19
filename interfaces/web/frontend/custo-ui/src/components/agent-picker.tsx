"use client";

import {
  memo,
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { Check, ChevronDown, Bot } from "lucide-react";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export type AgentOption = {
  id: string;
  name: string;
  description?: string;
};

export type AgentPickerProps = {
  agents: AgentOption[];
  value?: string;
  defaultValue?: string;
  onChange?: (agentId: string) => void;
  placeholder?: string;
  className?: string;
};

function Popover({
  trigger,
  children,
  open,
  onOpenChange,
}: {
  trigger: ReactNode;
  children: ReactNode;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const wrapRef = useRef<HTMLSpanElement | null>(null);

  useEffect(() => {
    if (!open) return;
    function onDocClick(e: MouseEvent) {
      if (!wrapRef.current) return;
      if (!wrapRef.current.contains(e.target as Node)) onOpenChange(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onOpenChange(false);
    }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open, onOpenChange]);

  return (
    <span ref={wrapRef} className="relative inline-flex">
      <span onClick={() => onOpenChange(!open)} className="inline-flex">
        {trigger}
      </span>
      {open && (
        <div
          role="dialog"
          className="absolute bottom-full left-0 z-50 mb-1.5 min-w-[180px] rounded-[10px] border border-border bg-popover p-1 shadow-lg outline-none text-foreground"
        >
          {children}
        </div>
      )}
    </span>
  );
}

export const AgentPicker = memo(function AgentPicker({
  agents,
  value,
  defaultValue,
  onChange,
  placeholder = "Auto",
  className,
}: AgentPickerProps) {
  const isControlled = value !== undefined;
  const [internalValue, setInternalValue] = useState(defaultValue);
  const activeId = isControlled ? value : internalValue;
  const activeAgent = agents.find((a) => a.id === activeId) ?? agents[0];
  const [open, setOpen] = useState(false);

  const handleSelect = useCallback(
    (id: string) => {
      if (!isControlled) setInternalValue(id);
      onChange?.(id);
      setOpen(false);
    },
    [isControlled, onChange],
  );

  return (
    <Popover
      open={open}
      onOpenChange={setOpen}
      trigger={
        <button
          type="button"
          className={cn(
            "inline-flex h-7 items-center gap-1.5 rounded-[6px] px-2 text-[12px] leading-4 text-muted-foreground transition-colors hover:bg-accent cursor-pointer",
            className,
          )}
          aria-label="Select agent"
        >
          <Bot className="size-3" />
          <span className="font-medium">
            {activeAgent?.name ?? placeholder}
          </span>
          <ChevronDown className="size-3 text-muted-foreground" />
        </button>
      }
    >
      {agents.map((agent) => {
        const isActive = agent.id === activeAgent?.id;
        return (
          <button
            key={agent.id}
            type="button"
            onClick={() => handleSelect(agent.id)}
            className={cn(
              "flex w-full items-center gap-2 rounded-[6px] px-2 py-1.5 text-left text-[12px] leading-4 text-foreground transition-colors hover:bg-accent cursor-pointer",
              isActive && "bg-accent",
            )}
          >
            <Bot className="size-3 shrink-0 text-muted-foreground" />
            <span className="flex-1 truncate">
              {agent.name}
              {agent.description && (
                <span className="ml-1 text-muted-foreground">
                  — {agent.description}
                </span>
              )}
            </span>
            {isActive && (
              <Check className="size-3.5 shrink-0 text-muted-foreground" />
            )}
          </button>
        );
      })}
    </Popover>
  );
});
