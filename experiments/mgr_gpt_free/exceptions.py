"""
Niestandardowe wyjątki dla systemu Finance Track.
Zapewniają spójną strukturę błędów w całej aplikacji.
"""


class FinanceException(Exception):
    """
    Bazowa klasa wyjątków dla systemu Finance Track.
    """

    def __init__(self, status_code: int, detail: str):
        """
        :param status_code: Kod HTTP błędu
        :param detail: Szczegółowy komunikat błędu
        """
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class AssetNotFoundException(FinanceException):
    """
    Wyjątek zgłaszany, gdy nie znaleziono aktywa.
    """

    def __init__(self, asset_id: str | None = None):
        detail = (
            f"Nie znaleziono aktywa (asset_id={asset_id})"
            if asset_id
            else "Brak aktywów w bazie danych"
        )
        super().__init__(status_code=404, detail=detail)


class DatabaseConnectionException(FinanceException):
    """
    Wyjątek zgłaszany przy problemach z bazą danych.
    """

    def __init__(self):
        super().__init__(
            status_code=500,
            detail="Błąd połączenia z bazą danych",
        )