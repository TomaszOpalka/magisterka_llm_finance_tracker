"""
Niestandardowe wyjątki dla systemu Finance Track.
Każdy wyjątek przenosi kod statusu HTTP oraz czytelny komunikat.
Wszystkie logi i komunikaty odwołują się do klucza głównego jako 'asset_id'.
"""

class FinanceException(Exception):
    """Bazowy wyjątek dla logiki biznesowej Finance Track."""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class AssetNotFoundException(FinanceException):
    """Rzucany, gdy żądany zasób (aktywo) nie istnieje."""
    def __init__(self, detail: str = "Aktywo o podanym asset_id nie zostało znalezione."):
        super().__init__(status_code=404, detail=detail)


class DatabaseConnectionException(FinanceException):
    """Rzucany w przypadku problemów z połączeniem do bazy danych."""
    def __init__(self, detail: str = "Błąd połączenia z bazą danych (finance.db)."):
        super().__init__(status_code=500, detail=detail)