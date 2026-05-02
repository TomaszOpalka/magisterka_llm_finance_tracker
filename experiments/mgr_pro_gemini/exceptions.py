class FinanceException(Exception):
    """
    Klasa bazowa dla wszystkich niestandardowych wyjątków w systemie Finance Track.
    Wymaga podania kodu statusu HTTP oraz szczegółowego komunikatu.
    """
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


class AssetNotFoundException(FinanceException):
    """
    Wyjątek zgłaszany w sytuacji, gdy żądany instrument finansowy 
    (lub lista instrumentów) nie zostanie odnaleziony w bazie danych.
    """
    def __init__(self, detail: str = "Nie znaleziono żądanego instrumentu finansowego (asset_id)."):
        super().__init__(status_code=404, detail=detail)


class DatabaseConnectionException(FinanceException):
    """
    Wyjątek zgłaszany, gdy wystąpi krytyczny problem z połączeniem 
    lub odczytem z bazy danych.
    """
    def __init__(self, detail: str = "Wystąpił błąd podczas komunikacji z bazą danych."):
        super().__init__(status_code=503, detail=detail)