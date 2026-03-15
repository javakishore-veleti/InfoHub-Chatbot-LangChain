from fastapi import APIRouter

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/health")
def get_chat_health() -> dict[str, str]:
    return {
        "module": "chat",
        "status": "not_implemented_yet",
    }

