class CsvValidationError(Exception):
    def __init__(
        self,
        message: str,
        row_number: int | None = None,
        field: str | None = None,
        value: str | None = None,
    ):
        self.message = message
        self.row_number = row_number
        self.field = field
        self.value = value


class TargetOneCError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_text: str | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(message)