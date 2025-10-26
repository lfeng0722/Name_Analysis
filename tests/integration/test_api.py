import pytest
from fastapi.testclient import TestClient
import types
# ------------------------------------------------
# Integration tests for the FastAPI application
# Assumes tests/conftest.py provides `app_client`
# ------------------------------------------------

@pytest.fixture(scope="module")
def client(app_client) -> TestClient:
    """Re-use a single TestClient instance per module for speed."""
    return app_client


@pytest.mark.integration
def test_docs_available(client: TestClient):
    """Basic health check: OpenAPI document should be available and titled correctly."""
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert r.json()["info"]["title"] == "TV Title Normalisation Service"


@pytest.mark.integration
def test_metrics_endpoint_exposes_prometheus_text(client: TestClient):
    """The /metrics endpoint should expose Prometheus text format and include default process metrics."""
    r = client.get("/metrics")
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("text/plain")
    body = r.text
    # A couple of common default metrics names from prometheus_client
    assert "python_info" in body
    assert "process_cpu_seconds_total" in body or "process_virtual_memory_bytes" in body


@pytest.mark.integration
def test_single_normalise_happy_path(client: TestClient):
    """Single endpoint happy path from the problem statement."""
    r = client.post("/normalise", json={"messy_title": "BILLY THE EXTERMINATOR-DAY (R)"})
    assert r.status_code == 200
    assert r.json() == {"clean_title": "BILLY THE EXTERMINATOR"}


@pytest.mark.integration
def test_single_normalise_validation_error(client: TestClient):
    """
    Missing required field should trigger FastAPI/Pydantic validation error.
    Using the contract ensures clients know they must send valid JSON.
    """
    r = client.post("/normalise", json={})
    assert r.status_code == 422


@pytest.mark.integration
def test_batch_normalise_happy_path(client: TestClient):
    """Batch endpoint happy path from the problem statement."""
    payload = {"messy_titles": ["GOTHAM -RPT", "HOT SEAT -5PM", "MIXOLOGY-EARLY(R)"]}
    r = client.post("/normalise-batch", json=payload)
    assert r.status_code == 200
    assert r.json()["clean_titles"] == ["GOTHAM", "HOT SEAT", "MIXOLOGY"]


@pytest.mark.integration
def test_batch_preserve_order_and_length(client: TestClient):
    """The batch endpoint should preserve input order and output length."""
    messy = ["A -RPT", "B -RPT", "C -RPT", "D -RPT"]
    r = client.post("/normalise-batch", json={"messy_titles": messy})
    assert r.status_code == 200
    clean = r.json()["clean_titles"]
    assert len(clean) == len(messy)
    assert clean == ["A", "B", "C", "D"]


@pytest.mark.integration
def test_batch_empty_list(client: TestClient):
    """Empty list is a valid request; expect an empty list in response."""
    r = client.post("/normalise-batch", json={"messy_titles": []})
    assert r.status_code == 200
    assert r.json()["clean_titles"] == []


@pytest.mark.integration
def test_batch_large_input(client: TestClient):
    """Large payload should still be processed correctly within memory/time limits."""
    messy = [f"TITLE{i} -RPT" for i in range(2000)]
    r = client.post("/normalise-batch", json={"messy_titles": messy})
    assert r.status_code == 200
    clean = r.json()["clean_titles"]
    assert clean[:3] == ["TITLE0", "TITLE1", "TITLE2"]
    assert len(clean) == 2000


@pytest.mark.integration
def test_content_type_must_be_json(client: TestClient):
    """
    Sending non-JSON payloads should not be accepted by contract.
    FastAPI typically responds with 422/415/400 depending on parsing.
    """
    r = client.post("/normalise", data="messy_title=SHOW -RPT")
    assert r.status_code in (400, 415, 422)


# ---------------------------
# Additional edge case tests
# ---------------------------

@pytest.mark.integration
def test_single_normalise_edge_combo_recursive(client: TestClient):
    """
    Edge combo: title contains DAY + number + FEED.
    Requires multiple passes (recursion) to fully clean.
    """
    r = client.post("/normalise", json={
        "messy_title": "SEVEN'S TENNIS: 2018 AUSTRALIAN OPEN-DAY 2 FEED2"
    })
    assert r.status_code == 200
    assert r.json()["clean_title"] == "SEVEN'S TENNIS: 2018 AUSTRALIAN OPEN"


@pytest.mark.integration
def test_single_normalise_s_d_rain_del(client: TestClient):
    """
    Edge combo: S/D tokens with optional 'RAIN DEL'.
    All suffix tokens should be stripped when they match the artifact's patterns.
    """
    r = client.post("/normalise", json={
        "messy_title": "SEVEN'S CRICKET: FOURTH TEST - AUSTRALIA V INDIA D4 S2 RAIN DEL"
    })
    assert r.status_code == 200
    assert r.json()["clean_title"] == "SEVEN'S CRICKET: FOURTH TEST - AUSTRALIA V INDIA"


@pytest.mark.integration
def test_batch_normalise_mixed_edge_cases(client: TestClient):
    """
    Batch: mixed edge inputs covering AM/PM, PART/EP, weekdays, S/D, prefix 'M-', DAY+num, and '(R)'.
    Expected outputs aligned with the artifact's real behavior.
    """
    payload = {
        "messy_titles": [
            "VET ON THE HILL -PM TX1",                               # '-PM' + 'TX1'
            "MILLION DOLLAR COLD CASE-PART 2",                       # 'PART 2'
            "THE BIG BANG THEORY-EP.2",                              # 'EP.2'
            "NINE NEWS LATE -THU",                                   # weekday then trailing LATE
            "SEVEN'S CRICKET: BIG BASH LEAGUE GRAND FINAL-S1",       # '-S1' is NOT removed
            "M- RESIDENT EVIL: APOCALYPSE-PM",                       # prefix + PM
            "SEVEN'S TENNIS: 2017 AUSTRALIAN OPEN - DAY 1",          # 'DAY 1'
            "BILLY THE EXTERMINATOR-DAY (R)",                        # '(R)'
        ]
    }
    r = client.post("/normalise-batch", json=payload)
    assert r.status_code == 200
    assert r.json()["clean_titles"] == [
        "VET ON THE HILL",
        "MILLION DOLLAR COLD CASE",
        "THE BIG BANG THEORY",
        "NINE NEWS",  # recursion removes trailing LATE after -THU is removed
        "SEVEN'S CRICKET: BIG BASH LEAGUE GRAND FINAL-S1",  # unchanged
        "RESIDENT EVIL: APOCALYPSE",
        "SEVEN'S TENNIS: 2017 AUSTRALIAN OPEN",
        "BILLY THE EXTERMINATOR",
    ]


@pytest.mark.integration
def test_batch_normalise_handles_empty_and_noise(client: TestClient):
    """
    Batch: includes an empty string and a 'mostly noise' sample.
    The artifact keeps leading 'S01 E02' because patterns expect a leading space before S/E tokens.
    """
    payload = {
        "messy_titles": [
            "",
            "M- S01 E02 -POST MATCH -RPT (R) 5PM"
        ]
    }
    r = client.post("/normalise-batch", json=payload)
    assert r.status_code == 200
    assert r.json()["clean_titles"] == ["", "S01 E02"]


@pytest.mark.integration
def test_single_normalise_internal_error(client, monkeypatch):
    """Force the endpoint to hit the except branch and return 500."""
    def boom(*_args, **_kwargs):
        raise RuntimeError("kaboom")

    # Patch the function as imported in app.main
    monkeypatch.setattr("app.main.normalise_title", boom, raising=True)

    r = client.post("/normalise", json={"messy_title": "ANY"})
    assert r.status_code == 500
    body = r.json()
    assert "detail" in body and "kaboom" in body["detail"]


@pytest.mark.integration
def test_batch_normalise_internal_error(client, monkeypatch):
    """Force the batch endpoint's error path and assert 500 + detail."""
    def boom(*_args, **_kwargs):
        raise RuntimeError("oh no")

    monkeypatch.setattr("app.main.normalise_title", boom, raising=True)

    r = client.post("/normalise-batch", json={"messy_titles": ["A -RPT", "B -RPT"]})
    assert r.status_code == 500
    body = r.json()
    assert "detail" in body and "oh no" in body["detail"]