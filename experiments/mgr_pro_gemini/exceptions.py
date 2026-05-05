class FinanceException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

class AssetNotFoundException(FinanceException):
    def __init__(self, detail: str = "Asset not found in the database."):
        super().__init__(status_code=404, detail=detail)

class DatabaseConnectionException(FinanceException):
    def __init__(self, detail: str = "Database connection error occurred."):
        super().__init__(status_code=503, detail=detail)

# New exception for yfinance or external API errors
class ExternalAPIException(FinanceException):
    """
    Raised when an external service (like yfinance) encounters a critical failure,
    such as network timeout or returning malformed data.
    """
    def __init__(self, detail: str = "External financial data provider is unavailable."):
        super().__init__(status_code=502, detail=detail)