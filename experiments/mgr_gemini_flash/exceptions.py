class FinanceException(Exception):
    """Bazowy wyjątek dla całego systemu Finance Track."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class AssetNotFoundException(FinanceException):
    """Wyjątek rzucany, gdy nie odnaleziono aktywa o danym asset_id lub lista jest pusta."""
    def __init__(self, message: str = "Nie odnaleziono zasobów finansowych"):
        super().__init__(message, status_code=404)

class DatabaseConnectionException(FinanceException):
    """Wyjątek rzucany w przypadku problemów z połączeniem z bazą danych."""
    def __init__(self, message: str = "Błąd połączenia z bazą danych"):
        super().__init__(message, status_code=503)