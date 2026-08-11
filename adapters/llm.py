from adapters.base import Adapter


class LlmAdapter(Adapter):

    #TODO to fix later stub
    @staticmethod
    def request(endpoint: str, payload: str):
        """
        Stub that "requests" to a local ollama endpoint on port 11434.
        Returns a fake response for now.
        """
        # In a real scenario, you'd use `requests.post()` or `httpx`, etc.
        # For now, just stub
        if endpoint.startswith("http://localhost:11434"):
            # Simulate a valid response from the ollama server
            return {"status": "success", "response": "This is a stubbed response from Ollama at 11434."}

        # Just echo back for any other endpoints
        return {"status": "error", "response": f"Endpoint {endpoint} not recognized in stub."}