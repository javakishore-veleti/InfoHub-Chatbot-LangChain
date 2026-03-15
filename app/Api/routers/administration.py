from fastapi import APIRouter

router = APIRouter(prefix="/administration", tags=["administration"])


@router.get("/health")
def get_administration_health() -> dict[str, str]:
    return {
        "module": "administration",
        "status": "not_implemented_yet",
    }

