from fastapi import FastAPI
from fastapi.testclient import TestClient

from ace_pro_api.errors import ApiError, install_error_handlers


def test_api_error_has_stable_shape() -> None:
    app = FastAPI()
    install_error_handlers(app)

    @app.get("/failure")
    async def failure() -> None:
        raise ApiError(status_code=409, code="example_conflict", message="Example conflict")

    response = TestClient(app).get("/failure")

    assert response.status_code == 409
    assert response.json() == {
        "error": {"code": "example_conflict", "message": "Example conflict"}
    }

