"""
Custom exceptions for the Finance Track system.
Each exception carries an HTTP status code and a human-readable detail message.
All references to the primary key use 'asset_id'.
"""

class FinanceException(Exception):
    """Base business logic exception for Finance Track."""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class AssetNotFoundException(FinanceException):
    """Raised when the requested asset (by asset_id) does not exist."""
    def __init__(self, detail: str = "Asset with the given asset_id was not found."):
        super().__init__(status_code=404, detail=detail)


class DatabaseConnectionException(FinanceException):
    """Raised when the database connection cannot be established."""
    def __init__(self, detail: str = "Database connection error (finance.db)."):
        super().__init__(status_code=500, detail=detail)


class StockDataException(FinanceException):
    """Raised when external stock data retrieval fails."""
    def __init__(self, detail: str = "Failed to retrieve stock data."):
        super().__init__(status_code=502, detail=detail)