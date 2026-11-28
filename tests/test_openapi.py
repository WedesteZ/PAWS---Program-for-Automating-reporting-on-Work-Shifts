"""Тесты доступности /health, Swagger UI и корректности схемы OpenAPI."""

from fastapi.testclient import TestClient

HTML_ROUTES = {
    "/",
    "/login",
    "/logout",
    "/shifts/add",
    "/employees",
    "/employees/add",
    "/reports",
    "/reports/generate",
}


def test_health_endpoint(api_client: TestClient) -> None:
    """Проверяет, что /health отвечает 200 OK."""
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_swagger_docs_available(api_client: TestClient) -> None:
    """Проверяет доступность интерактивной документации /docs."""
    response = api_client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "PAWS API" in response.text


def test_openapi_metadata_and_paths(api_client: TestClient) -> None:
    """Проверяет метаданные OpenAPI и скрытие HTML-маршрутов из схемы."""
    response = api_client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert schema["info"]["title"] == "PAWS API"
    assert schema["info"]["version"] == "0.1.0"

    paths = set(schema["paths"].keys())
    assert "/health" in paths
    assert HTML_ROUTES.isdisjoint(paths)

    api_paths = paths - {"/health"}
    assert api_paths, "В схеме OpenAPI должны присутствовать маршруты /api/*"
    assert all(path.startswith("/api/") for path in api_paths)


def test_openapi_schemas_have_no_legacy_dto_names(api_client: TestClient) -> None:
    """Проверяет, что в OpenAPI нет устаревших имён моделей с суффиксом DTO."""
    schema = api_client.get("/openapi.json").json()
    schema_names = list(schema.get("components", {}).get("schemas", {}).keys())

    assert schema_names
    assert all(not name.endswith("DTO") for name in schema_names)
