from fastapi import APIRouter

router = APIRouter(prefix="/model-build", tags=["model-build"])


@router.get("/health")
def get_model_build_health() -> dict[str, str]:
    return {
        "module": "model_build",
        "status": "not_implemented_yet",
    }

