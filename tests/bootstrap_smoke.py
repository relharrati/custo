"""Comprehensive smoke test of the Custo bootstrap."""
import asyncio
import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent


async def run_all():
    print("=" * 60)
    print("  CUSTO BOOTSTRAP VERIFICATION")
    print("=" * 60)
    print()

    results = {}

    # 1. Agent IPC
    print("[1/6] Agent IPC test...")
    import subprocess
    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "tests" / "test_agent_ipc.py")],
        cwd=str(ROOT),
        env={**__import__('os').environ, "PYTHONPATH": str(ROOT)},
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    out, err = proc.communicate(timeout=30)
    results["agent_ipc"] = "PASS" in out
    print(f"      {'[OK]' if results['agent_ipc'] else '[FAIL]'}")

    # 2. Daemon startup
    print("[2/6] Daemon startup test...")
    from daemon.supervisor import Supervisor
    from agents.registry import get_registry
    registry = get_registry(ROOT)
    await registry.load()
    sup = Supervisor(ROOT)
    await sup.start()
    await asyncio.sleep(2)
    status = sup.get_agent_status()
    all_running = all(s["running"] for s in status.values())
    results["daemon"] = all_running
    print(f"      Agents: {[f'{k}:{v['running']}' for k,v in status.items()]}")
    await sup.stop()
    print(f"      {'[OK]' if all_running else '[FAIL]'}")

    # 3. Chat flow
    print("[3/6] Chat flow test...")
    sys.path.insert(0, str(ROOT))
    from agents.main.agent import MainAgent
    from sessions.manager import SessionManager
    agent = MainAgent(ROOT)
    await agent.start()
    sm = SessionManager(ROOT)
    sess = sm.create_session()
    task = {"type": "user_message", "content": "hello", "session_id": sess["id"]}
    res = await agent.process_task(task)
    results["chat_flow"] = res.get("type") == "response" and len(res.get("content", "")) > 0
    await agent.stop()
    print(f"      Response: {res.get('content', '')[:50]}")
    print(f"      {'[OK]' if results['chat_flow'] else '[FAIL]'}")

    # 4. LLM provider factory
    print("[4/6] LLM provider factory...")
    from system.llm import get_provider
    from system.llm.ollama import OllamaProvider
    p = get_provider({"provider": "auto"})
    ram = OllamaProvider.detect_ram_gb()
    recs = OllamaProvider.recommend_models(ram)
    results["llm_provider"] = p is not None and ram >= 0 and len(recs) >= 2
    print(f"      RAM: {ram}GB, tiers: {list(recs.keys())}")
    print(f"      {'[OK]' if results['llm_provider'] else '[FAIL]'}")

    # 5. Config loading
    print("[5/6] Config system...")
    from system.config import load_config, save_config
    cfg = load_config(ROOT)
    results["config"] = "llm" in cfg and "provider" in cfg["llm"]
    print(f"      llm.provider = {cfg.get('llm', {}).get('provider', 'missing')}")
    print(f"      {'[OK]' if results['config'] else '[FAIL]'}")

    # 6. CLI commands
    print("[6/6] CLI commands...")
    import subprocess
    env = {**__import__('os').environ, "PYTHONPATH": str(ROOT)}
    p = subprocess.Popen(
        [sys.executable, "-c", "from interfaces.terminal.cli import main; import sys; sys.argv=['custo','version']; main()"],
        cwd=str(ROOT), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    out, _ = p.communicate(timeout=10)
    results["cli"] = "Custo" in out
    print(f"      Output: {out.strip()[:40]}")
    print(f"      {'[OK]' if results['cli'] else '[FAIL]'}")

    print()
    print("=" * 60)
    all_ok = all(results.values())
    for k, v in results.items():
        status = "[OK]" if v else "[FAIL]"
        print(f"  {status} {k}")
    print("=" * 60)
    print()
    if all_ok:
        print("  ALL CHECKS PASSED — Custo is ready!")
        print()
        print("  Start chatting:")
        print("    py custo chat")
    else:
        print("  Some checks failed — review above")
    return all_ok


if __name__ == "__main__":
    try:
        ok = asyncio.run(asyncio.wait_for(run_all(), timeout=60))
        sys.exit(0 if ok else 1)
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"\nFATAL: {e}")
        sys.exit(1)
