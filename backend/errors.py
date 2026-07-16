from fastapi import HTTPException


def api_error(status_code: int, code: str, message: str, **meta) -> HTTPException:
    """표준 에러 응답 { error: { code, message, ...meta } } 을 만든다."""
    detail = {"error": {"code": code, "message": message, **meta}}
    return HTTPException(status_code=status_code, detail=detail)
