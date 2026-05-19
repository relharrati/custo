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
import { Check, ChevronDown, Search, Star, Loader2, Plus, Settings, X } from "lucide-react";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export type ModelOption = {
  id: string;
  name: string;
  provider: string;
  version?: string;
  favorite?: boolean;
};

export type ModelPickerProps = {
  models: ModelOption[];
  value?: string;
  defaultValue?: string;
  onChange?: (modelId: string) => void;
  placeholder?: string;
  className?: string;
  onAddProvider?: () => void;
  onConfigure?: () => void;
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
          className="absolute bottom-full left-0 z-50 mb-1.5 w-[300px] rounded-[10px] border border-border bg-popover shadow-lg outline-none text-foreground overflow-hidden"
        >
          {children}
        </div>
      )}
    </span>
  );
}

function Switch({ checked, onCheckedChange, size = "sm" }: { checked: boolean; onCheckedChange: (v: boolean) => void; size?: "sm" | "xs" }) {
  const s = size === "xs" ? "w-8 h-4" : "w-9 h-5";
  const dot = size === "xs" ? "size-3" : "size-4";
  const translate = size === "xs" ? "translate-x-[16px]" : "translate-x-[18px]";
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onCheckedChange(!checked)}
      className={cn(
        "relative inline-flex shrink-0 rounded-full transition-all duration-300 border",
        s,
        checked
          ? "bg-emerald-500/20 border-emerald-500/50 shadow-[0_0_8px_rgba(16,185,129,0.3)]"
          : "bg-muted/50 border-muted-foreground/20"
      )}
    >
      <span
        className={cn(
          "absolute top-0.5 left-0.5 rounded-full shadow-sm transition-all duration-300",
          dot,
          checked
            ? cn(translate, "bg-emerald-400 shadow-[0_0_4px_rgba(16,185,129,0.6)]")
            : "translate-x-0 bg-muted-foreground/60"
        )}
      />
    </button>
  );
}

export const ModelPicker = memo(function ModelPicker({
  models,
  value,
  defaultValue,
  onChange,
  placeholder = "Auto",
  className,
  onAddProvider,
  onConfigure,
}: ModelPickerProps) {
  const isControlled = value !== undefined;
  const [internalValue, setInternalValue] = useState(defaultValue);
  const activeId = isControlled ? value : internalValue;
  const activeModel = models.find((m) => m.id === activeId) ?? models[0];
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const searchRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) {
      setSearch("");
      setTimeout(() => searchRef.current?.focus(), 50);
      if (listRef.current) listRef.current.scrollTop = 0;
    }
  }, [open]);

  const handleSelect = useCallback(
    (id: string) => {
      if (!isControlled) setInternalValue(id);
      onChange?.(id);
      setOpen(false);
    },
    [isControlled, onChange],
  );

  const favorites = models.filter((m) => m.favorite);
  const filtered = models.filter(
    (m) =>
      !m.favorite &&
      (m.name.toLowerCase().includes(search.toLowerCase()) ||
        m.provider.toLowerCase().includes(search.toLowerCase()))
  );

  const favFiltered = search
    ? favorites.filter(
        (m) =>
          m.name.toLowerCase().includes(search.toLowerCase()) ||
          m.provider.toLowerCase().includes(search.toLowerCase())
      )
    : favorites;

  const showFavorites = favFiltered.length > 0 && !search;

  function ModelRow({ model }: { model: ModelOption }) {
    const isActive = model.id === activeModel?.id;
    return (
      <button
        type="button"
        onClick={() => handleSelect(model.id)}
        className={cn(
          "flex w-full items-center gap-2 rounded-[6px] px-2.5 py-1.5 text-left text-[13px] leading-4 text-foreground transition-colors hover:bg-accent cursor-pointer",
          isActive && "bg-accent",
        )}
      >
        <span className="flex-1 min-w-0 truncate">{model.name}{model.version && <span className="text-muted-foreground"> {model.version}</span>}</span>
        {isActive && <Check className="size-3.5 shrink-0 text-muted-foreground" />}
      </button>
    );
  }

  const groupedByProvider = filtered.reduce<Record<string, ModelOption[]>>((acc, m) => {
    if (!acc[m.provider]) acc[m.provider] = [];
    acc[m.provider].push(m);
    return acc;
  }, {});

  const favGrouped = favFiltered.reduce<Record<string, ModelOption[]>>((acc, m) => {
    if (!acc[m.provider]) acc[m.provider] = [];
    acc[m.provider].push(m);
    return acc;
  }, {});

  return (
    <Popover
      open={open}
      onOpenChange={setOpen}
      trigger={
        <button
          type="button"
          className={cn(
            "inline-flex h-7 items-center gap-1 rounded-[6px] px-2 text-[12px] leading-4 text-muted-foreground transition-colors hover:bg-accent cursor-pointer",
            className,
          )}
          aria-label="Select model"
        >
          <span className="font-medium">
            {activeModel?.name ?? placeholder}
          </span>
          {activeModel?.version && (
            <span className="font-normal text-muted-foreground/60">
              {activeModel.version}
            </span>
          )}
          <ChevronDown className="size-3 text-muted-foreground" />
        </button>
      }
    >
      <div className="p-1.5 border-b border-border">
        <div className="flex items-center gap-1">
          <div className="relative flex-1">
            <Search className="absolute left-1.5 top-1/2 -translate-y-1/2 size-3 text-muted-foreground pointer-events-none" />
            <input
              ref={searchRef}
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search..."
              className="w-full h-6 pl-6 pr-2 rounded-[5px] bg-muted/50 text-[11px] text-foreground placeholder:text-muted-foreground outline-none border border-transparent focus:border-border transition-colors"
            />
          </div>
          <button type="button" onClick={onAddProvider} className="inline-flex size-6 items-center justify-center rounded-[5px] text-muted-foreground hover:bg-accent transition-colors" title="Add provider">
            <Plus className="size-3.5" />
          </button>
          <button type="button" onClick={onConfigure} className="inline-flex size-6 items-center justify-center rounded-[5px] text-muted-foreground hover:bg-accent transition-colors" title="Configure models">
            <Settings className="size-3.5" />
          </button>
        </div>
      </div>
      <div ref={listRef} className="max-h-[280px] overflow-y-auto p-1 [&::-webkit-scrollbar]:w-1 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-muted-foreground/20 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:hover:bg-muted-foreground/40">
        {models.length === 0 ? (
          <div className="flex items-center gap-2 px-2.5 py-6 text-[12px] text-muted-foreground justify-center">
            <Loader2 className="size-3.5 animate-spin" />
            <span>Loading models...</span>
          </div>
        ) : (
          <>
            {showFavorites && (
              <div className="mb-1">
                <div className="flex items-center gap-1.5 px-2.5 py-1 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                  <Star className="size-3" />
                  <span>Favorites</span>
                </div>
                {Object.entries(favGrouped).map(([provider, providerModels]) => (
                  <div key={provider}>
                    <div className="px-2.5 py-0.5 text-[11px] font-medium text-muted-foreground">{provider}</div>
                    {providerModels.map((model) => (
                      <ModelRow key={model.id} model={model} />
                    ))}
                  </div>
                ))}
              </div>
            )}
            <div>
              {search && (
                <div className="px-2.5 py-1 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                  Results ({filtered.length})
                </div>
              )}
              {!search && (
                <div className="px-2.5 py-1 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                  Available Models
                </div>
              )}
              {Object.entries(groupedByProvider).map(([provider, providerModels]) => (
                <div key={provider}>
                  <div className="px-2.5 py-0.5 text-[11px] font-medium text-muted-foreground">{provider}</div>
                  {providerModels.map((model) => (
                    <ModelRow key={model.id} model={model} />
                  ))}
                </div>
              ))}
              {filtered.length === 0 && search && (
                <div className="px-2.5 py-3 text-[12px] text-muted-foreground text-center">
                  No models found
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </Popover>
  );
});

export type ProviderConfig = {
  id: string;
  name: string;
  enabled: boolean;
  models: { id: string; name: string; enabled: boolean }[];
};

export function ProviderConfigDialog({
  providers,
  open,
  onOpenChange,
  onChange,
}: {
  providers: ProviderConfig[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onChange: (providers: ProviderConfig[]) => void;
}) {
  if (!open) return null;

  function toggleProvider(id: string) {
    onChange(
      providers.map((p) =>
        p.id === id ? { ...p, enabled: !p.enabled, models: p.models.map((m) => ({ ...m, enabled: !p.enabled })) } : p
      )
    );
  }

  function toggleModel(providerId: string, modelId: string) {
    onChange(
      providers.map((p) =>
        p.id === providerId
          ? { ...p, models: p.models.map((m) => (m.id === modelId ? { ...m, enabled: !m.enabled } : m)) }
          : p
      )
    );
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => onOpenChange(false)}>
      <div
        className="w-[440px] max-h-[80vh] rounded-[12px] border border-border bg-popover shadow-2xl overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <h3 className="text-sm font-semibold">Configure Providers</h3>
          <button onClick={() => onOpenChange(false)} className="inline-flex size-7 items-center justify-center rounded-md text-muted-foreground hover:bg-accent transition-colors">
            <X className="size-4" />
          </button>
        </div>
        <div className="overflow-y-auto p-3 space-y-2 [&::-webkit-scrollbar]:w-1 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-muted-foreground/20 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:hover:bg-muted-foreground/40">
          {providers.map((provider) => (
            <div key={provider.id} className="rounded-lg border border-border overflow-hidden">
              <div className="flex items-center justify-between px-3 py-2 bg-muted/40">
                <span className="text-xs font-semibold">{provider.name}</span>
                <Switch checked={provider.enabled} onCheckedChange={() => toggleProvider(provider.id)} size="xs" />
              </div>
              {provider.enabled && (
                <div className="divide-y divide-border/50">
                  {provider.models.map((model) => (
                    <div key={model.id} className="flex items-center justify-between px-3 py-1.5">
                      <span className="text-[12px] text-foreground">{model.name}</span>
                      <Switch checked={model.enabled} onCheckedChange={() => toggleModel(provider.id, model.id)} size="xs" />
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
