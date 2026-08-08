from __future__ import annotations


class APIProblem(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        evaluation_id: str | None = None,
        response_status: str = "error",
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.evaluation_id = evaluation_id
        self.response_status = response_status
