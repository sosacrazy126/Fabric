class StorageService:
    def __init__(self):
        self.outputs = []

    def add_output(self, output: dict):
        self.outputs.append(output)

    def get_outputs(self):
        return self.outputs