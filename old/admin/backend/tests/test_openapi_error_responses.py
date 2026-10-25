from fastapi.testclient import TestClient


def test_v1_routes_declare_common_error_response_schema(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()

    responses = schema["paths"]["/api/v1/articles"]["get"]["responses"]

    for status_code in ["400", "401", "404", "409", "422", "428", "500"]:
        assert responses[status_code]["content"]["application/json"]["schema"]["$ref"] == (
            "#/components/schemas/ErrorResponseDTO"
        )
