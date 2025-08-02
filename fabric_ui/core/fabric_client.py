# Minimal stub of FabricClient for scaffolding.

class FabricClient:
    def __init__(self):
        pass

    def execute_pattern(self, pattern: str, input_text: str):
        # Stub - just echoes for now
        return {"success": True, "output": f"Pattern: {pattern}\nInput: {input_text}"}

    def get_status(self):
        # Minimal status info
        return {"fabric_installed": True, "version": "stub-0.0.1"}

    def get_providers(self):
        # Minimal provider stub
        return ["OpenAI", "Anthropic"]

    def get_patterns(self):
        # Minimal pattern stub
        return ["summarize", "analyze", "improve"]