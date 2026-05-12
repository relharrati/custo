"""Hardcoded fallback provider — pattern-matched responses for bootstrap."""

class HardcodedProvider:
    """Bootstrap fallback — pattern-matched responses only."""

    def __init__(self):
        self._model = "hardcoded (bootstrap)"

    async def generate(self, prompt: str, **kwargs) -> str:
        p = prompt.lower()

        # Extract user message
        user_msg = prompt
        for prefix in ["user:", "human:", "you:"]:
            if prefix in p:
                parts = prompt.split(prefix, 1)
                if len(parts) > 1:
                    user_msg = parts[1].strip()
                    break

        if any(w in p for w in ["hello", "hi", "hey", "greet"]):
            return "Hello! I'm Custo, your autonomous digital operator. I remember, plan, act, reflect, and improve. How can I help you today?"
        if "help" in p:
            return ("I can help you with:\n"
                    "- Task management and planning\n"
                    "- Memory and information retrieval\n"
                    "- Code implementation and debugging\n"
                    "- Research and documentation\n"
                    "- Project coordination")
        if "status" in p:
            return "I'm operational. The autonomous operator system is running normally. What would you like to do?"
        if any(w in p for w in ["what can you do", "capabilities", "features"]):
            return ("Custo keeps track of your tasks, remembers important information, "
                    "and helps you get things done. I can plan work, write code, research topics, "
                    "and reflect on past interactions to improve over time.")
        if any(w in p for w in ["who are you", "identity", "name"]):
            return "I'm Custo — an AI-augmented operator designed to remember, plan, act, reflect, and improve."

        if "?" in prompt and len(user_msg) < 50:
            return ("That's a good question. To give you a more detailed response, "
                    "I'll need a language model connected. Set this up with one of:\n\n"
                    "  Ollama:    ollama pull qwen2.5-coder:1.5b\n"
                    "  LM Studio: Load a GGUF model in LM Studio\n"
                    "  vLLM:      python -m vllm.entrypoints.openai.api_server --model <path>\n\n"
                    "Then edit system/config.yaml → llm.provider or run the setup wizard:\n"
                    "  py setup/init_config.py --wizard")

        return (f"I received: '{user_msg[:60]}'. "
                "(Bootstrap mode — connect an LLM provider for full responses via "
                "system/config.yaml → llm.provider or run `py setup/init_config.py --wizard`.)")

    def is_available(self) -> bool:
        return True

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return "Hardcoded (Bootstrap)"
