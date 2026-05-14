from fastapi import HTTPException


def structured_error(status_code: int, code: str, message: str, correlation_id: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"error": {"code": code, "message": message, "correlation_id": correlation_id}},
    )
