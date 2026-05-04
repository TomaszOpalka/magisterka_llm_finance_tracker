"""
Moduł zawierający niestandardowe wyjątki biznesowe dla systemu Finance Track.
Zapewnia spójną obsługę błędów w całym API.
"""

class FinanceException(Exception):
    """
    Klasa bazowa dla wszystkich wyjątków biznesowych w systemie Finance Track.
    """
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AssetNotFoundException(FinanceException):
    """
    Wyjątek rzucany gdy aktywo o podanym asset_id nie zostanie znalezione.
    """
    def __init__(self, asset_id: str):
        message = f"Aktywo o asset_id '{asset_id}' nie zostało znalezione w bazie danych."
        super().__init__(message, status_code=404)


class DatabaseConnectionException(FinanceException):
    """
    Wyjątek rzucany w przypadku problemów z połączeniem lub operacją na bazie danych.
    """
    def __init__(self, detail: str = "Błąd połączenia z bazą danych"):
        super().__init__(detail, status_code=500)