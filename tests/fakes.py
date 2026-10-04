class FakeMessage:
    def __init__(self, content: str):
        self.content = content


class FakeAgent:
    def __init__(self, content: str):
        self._content = content
        self.calls = []

    def invoke(self, payload):
        self.calls.append(payload)
        return {"messages": [FakeMessage(self._content)]}


class FakeChain:
    def __init__(self, output: str):
        self._output = output
        self.calls = []

    def invoke(self, payload):
        self.calls.append(payload)
        return self._output
