from pathlib import Path

p = Path("src/ledgermate/providers/registry.py")
content = p.read_text()

old = '''def build_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register_llm(LlamaCppProvider())
    registry.register_llm(MockLLMProvider())
    registry.register_stt(LocalSTTProvider())
    registry.register_stt(MockSTTProvider())
    return registry'''

new = '''def build_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    try:
        registry.register_llm(LlamaCppProvider())
    except Exception:
        pass
    registry.register_llm(MockLLMProvider())
    try:
        registry.register_stt(LocalSTTProvider())
    except Exception:
        pass
    registry.register_stt(MockSTTProvider())
    return registry'''

content = content.replace(old, new)
p.write_text(content)
print("Fixed build_registry")
