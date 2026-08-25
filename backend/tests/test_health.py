def test_health(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_test_client_is_served(client) -> None:
    response = client.get("/test-client")

    assert response.status_code == 200
    assert "Ace Pro upload test" in response.text
    assert "ace-pro-upload-session" in response.text


def test_metrics_are_exposed(client) -> None:
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "ace_pro_http_requests_total" in response.text
    assert 'route="/health"' in response.text
