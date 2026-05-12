from fastapi.testclient import TestClient

from Backend.api.server import create_app


def test_api_endpoints():
    app = create_app()

    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "online"
        assert health.json()["graph_loaded"] is True

        graph = client.get("/api/graph")
        assert graph.status_code == 200
        graph_payload = graph.json()
        assert graph_payload["nodes"]
        assert graph_payload["edges"]

        route = client.post(
            "/api/route/dijkstra",
            json={
                "source": "7",
                "destination": "4",
                "time_period": "morning",
                "mode": "normal",
            },
        )
        assert route.status_code == 200
        route_payload = route.json()
        assert route_payload["path"][0] == "7"
        assert route_payload["path"][-1] == "4"
        assert route_payload["distance"] > 0
        assert route_payload["path_coordinates"]

        compare = client.post(
            "/api/route/compare",
            json={
                "source": "7",
                "destination": "4",
                "time_period": "morning",
                "mode": "normal",
            },
        )
        assert compare.status_code == 200
        assert compare.json()["winner"] in {"astar", "dijkstra", "tie"}

        mst = client.get("/api/mst")
        assert mst.status_code == 200
        assert "total_cost" in mst.json()

        traffic = client.post(
            "/api/traffic/optimize",
            json={"time_period": "morning", "mode": "normal"},
        )
        assert traffic.status_code == 200
        assert "signal_plan" in traffic.json()

        transit = client.post(
            "/api/transit/optimize",
            json={"time_period": "morning", "capacity": 8},
        )
        assert transit.status_code == 200
        assert "schedule" in transit.json()
        assert "allocations" in transit.json()

        ml = client.post(
            "/api/ml/predict",
            json={
                "source": "7",
                "destination": "4",
                "time_period": "morning",
                "prediction_horizon": 30,
            },
        )
        assert ml.status_code == 200
        assert ml.json()["trend_data"]


def test_invalid_route_request_returns_json_error():
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/route/dijkstra",
            json={
                "source": "7",
                "destination": "7",
                "time_period": "morning",
                "mode": "normal",
            },
        )

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "same_source_destination"
