"""Test LLM provider factory and RAM detection."""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def test_factory_and_ollama():
    from system.llm import get_provider
    from system.llm.ollama import OllamaProvider

    # 1. RAM detection
    ram = OllamaProvider.detect_ram_gb()
    print(f"[TEST] Detected RAM: {ram} GB")
    assert ram >= 0, "RAM must be non-negative"

    # 2. Model recommendations - returns dict with tier keys
    recs = OllamaProvider.recommend_models(ram)
    print(f"[TEST] Recommendation tiers: {list(recs.keys())}")
    assert len(recs) >= 2, "Should have at least minimal + one tier"
    nonempty = sum(1 for v in recs.values() if v)
    print(f"[TEST] Non-empty tiers: {nonempty}")

    # 3. Hardcoded provider
    p_hard = get_provider({"provider": "hardcoded", "model": "none"})
    print(f"[TEST] Hardcoded: {p_hard.provider_name} / {p_hard.model_name}")
    assert p_hard.provider_name == "Hardcoded (Bootstrap)"

    # 4. Ollama provider (even if daemon not running)
    p_ollama = get_provider({"provider": "ollama", "model": "qwen2.5-coder:1.5b"})
    print(f"[TEST] Ollama: {p_ollama.provider_name} / {p_ollama.model_name}")
    assert p_ollama.model_name == "qwen2.5-coder:1.5b"

    # 5. Test Ollama generate (will fail but shouldn't crash)
    async def quick_gen():
        result = await p_ollama.generate("say hello")
        print(f"[TEST] Ollama generate result: {result[:60]}")
        return result

    try:
        asyncio.run(quick_gen())
    except Exception as e:
        print(f"[TEST] Ollama generate expected to fail if daemon not running: {type(e).__name__}")

    print("[TEST] All LLM provider tests passed")
    return True


if __name__ == "__main__":
    try:
        ok = test_factory_and_ollama()
        print("\n[RESULT]", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"\n[RESULT] FAIL - {e}")
        sys.exit(1)
