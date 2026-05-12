"""Model registry — fetches model recommendations from models.dev API with local fallback."""

import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, List, Tuple


# Local fallback models when API is unreachable
LOCAL_FALLBACK = {
    "ollama": {
        "small": [
            ("qwen2.5-coder:1.5b", "Qwen Coder 1.5B", "~1.1 GB", "Excellent code"),
            ("gemma3:1b", "Gemma 3 1B", "~790 MB", "Fast and light"),
            ("llama3.2:1b", "Llama 3.2 1B", "~670 MB", "Good general"),
        ],
        "medium": [
            ("qwen2.5-coder:7b", "Qwen Coder 7B", "~4.5 GB", "Strong coding"),
            ("gemma3:4b", "Gemma 3 4B", "~2.6 GB", "Balanced"),
            ("llama3.2:3b", "Llama 3.2 3B", "~2.0 GB", "Quick & capable"),
        ],
        "large": [
            ("qwen2.5:14b", "Qwen 14B", "~8.8 GB", "Powerful"),
            ("llama3.1:8b", "Llama 3.1 8B", "~4.9 GB", "Strong general"),
        ],
        "minimal": [
            ("phi4-mini:3b", "Phi-4 Mini 3B", "~2.1 GB", "Tiny but capable"),
        ]
    }
}


def fetch_models(force_refresh: bool = False, timeout: int = 10) -> Optional[Dict]:
    """
    Fetch model list from models.dev API.
    Returns full JSON or None on failure.
    Caches to .cache/models.json for 6 hours.
    """
    cache_dir = Path.home() / ".cache" / "custo"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / "models.json"

    # Check cache
    if not force_refresh and cache_file.exists():
        try:
            cache_age = (Path().stat().st_mtime if False else 0)  # placeholder
            import time
            age = time.time() - cache_file.stat().st_mtime
            if age < (6 * 3600):  # 6 hour TTL
                return json.loads(cache_file.read_text())
        except Exception:
            pass

    # MODELS_DEV_API_JSON allows pointing to mirror
    api_url = os.environ.get("MODELS_DEV_API_JSON", "https://models.dev/api.json")

    try:
        req = urllib.request.Request(
            str(api_url),
            headers={"User-Agent": "Custo/1.0", "Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            cache_file.write_text(json.dumps(data, indent=2))
            return data
    except Exception as e:
        print(f"[MODELS] API fetch failed: {e}")
        return None


def filter_ollama_models(models_data: Dict, min_ram_gb: int = 0, max_ram_gb: int = 32) -> List[Tuple]:
    """
    Filter models.dev data for Ollama-compatible local models.
    Returns list of (model_id, display_name, size_estimate, note) tuples.
    """
    results = []
    all_models = models_data.get("models", {})

    # Size mapping in GB (approximate, based on parameter count)
    SIZE_MAP = {
        "1b": "~670 MB", "1.5b": "~1.1 GB", "2b": "~1.5 GB", "3b": "~2.0 GB",
        "4b": "~2.6 GB", "5b": "~3.3 GB", "7b": "~4.5 GB", "8b": "~5.0 GB",
        "14b": "~8.8 GB", "16b": "~10 GB", "20b": "~12 GB", "32b": "~20 GB",
        "70b": "~40 GB", "72b": "~45 GB", "128b": "~80 GB", "400b": "~240 GB",
    }

    # Helper: estimate size from model ID
    def est_size(model_id: str) -> str:
        lid = model_id.lower()
        for size_str, display in SIZE_MAP.items():
            if size_str in lid:
                return display
        return "~?"

    for mid, mdef in all_models.items():
        # Must be local-run capable and popular enough
        if not mdef.get("local_run", False):
            continue

        # Skip models with API-only endpoints (no local inference)
        if mdef.get("local") is False:
            continue

        # Provider filtering — look for common local provider families
        vendor = mdef.get("vendor", "").lower()
        family = mdef.get("family", "").lower()
        if not any(p in vendor for p in ("meta", "google", "microsoft", "qwen", "deepseek", "mistral", "gemma", "phi", "llama")):
            continue

        # Estimate context
        context = mdef.get("limit", {}).get("context", 0)
        if context < 1024:
            continue

        model_id = mid
        name = mdef.get("name", mid)
        size_est = est_size(mid)

        # Add note based on family
        note = "Local model"
        if "qwen" in family or "qwen" in mid.lower():
            note = "Strong code & multilingual"
        elif "llama" in family:
            note = "Meta general purpose"
        elif "gemma" in family:
            note = "Google lightweight"
        elif "phi" in family:
            note = "Microsoft tiny"
        elif "mistral" in family:
            note = "French open-weight"
        elif "deepseek" in family:
            note = "Code focused"

        results.append((model_id, name, size_est, note))

    # Sort: prefer smaller, then by name
    def sort_key(item):
        size = item[2]
        # Convert "~1.1 GB" → 1.1, "~670 MB" → 0.67
        try:
            if "GB" in size:
                val = float(size.replace("~", "").replace("GB", "").strip())
            elif "MB" in size:
                val = float(size.replace("~", "").replace("MB", "").strip()) / 1024
            else:
                val = 0
        except ValueError:
            val = 999
        return (val, item[0])

    results.sort(key=sort_key)
    return results


def get_recommended_models(ram_gb: int, provider: str = "ollama") -> Dict[str, List[Tuple]]:
    """
    Return tiered model recommendations based on available RAM.

    Returns dict: {tier_name: [(model_id, display_name, size, note), ...]}
    tiers: minimal, small, medium, large
    """
    cache = None
    try:
        cache = fetch_models(timeout=8)
    except Exception:
        cache = None

    if cache:
        filtered = filter_ollama_models(cache, min_ram_gb=ram_gb * 0.5, max_ram_gb=ram_gb * 2)
    else:
        # Local fallback
        filtered = [(mid, name, size, note) for tier in ["small", "medium", "large", "minimal"]
                   for mid, name, size, note in LOCAL_FALLBACK["ollama"].get(tier, [])]

    # Build tiers
    tiers: Dict[str, List[Tuple]] = {"minimal": [], "small": [], "medium": [], "large": []}

    for model_id, name, size, note in filtered:
        # Rough sizing classification
        gb_est = 0
        try:
            if "GB" in size:
                gb_est = float(size.replace("~","").replace("GB","").strip())
            elif "MB" in size:
                gb_est = float(size.replace("~","").replace("MB","").strip()) / 1024
        except ValueError:
            gb_est = 999

        # Assign to tier - ensure OS + overhead fits
        if gb_est <= 1.5 or (ram_gb < 4 and gb_est <= ram_gb * 0.6):
            tiers["minimal"].append((model_id, name, size, note))
        elif gb_est <= 3.5:
            tiers["small"].append((model_id, name, size, note))
        elif gb_est <= 8:
            tiers["medium"].append((model_id, name, size, note))
        else:
            tiers["large"].append((model_id, name, size, note))

    # Ensure each tier has at least one option (fall back to local if empty)
    if not tiers["minimal"]:
        tiers["minimal"] = LOCAL_FALLBACK["ollama"]["minimal"]
    if not tiers["small"]:
        tiers["small"] = LOCAL_FALLBACK["ollama"]["small"]
    if not tiers["medium"]:
        tiers["medium"] = LOCAL_FALLBACK["ollama"]["medium"]
    if not tiers["large"]:
        tiers["large"] = LOCAL_FALLBACK["ollama"]["large"]

    return tiers


if __name__ == "__main__":
    # Quick test
    ram = 16
    print(f"RAM: {ram} GB")
    recs = get_recommended_models(ram)
    for tier, models in recs.items():
        print(f"\n{tier.upper()}:")
        for mid, name, size, note in models[:3]:
            print(f"  {mid:35s} {size:10s} — {note}")
