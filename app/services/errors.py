class ProviderAPIError(Exception):
    def __init__(
        self,
        provider: str,
        status_code: int = 500,
        message: str = "Provider request failed",
        detail: str = "",
    ) -> None:
        self.provider = provider
        self.status_code = status_code
        self.message = message
        self.detail = detail
        super().__init__(f"{provider}: {message} ({detail})")
