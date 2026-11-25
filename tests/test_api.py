"""API tests using an isolated in-memory SQLite database."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.geo import haversine_km
from app.main import app

BRUSSELS = {"name": "Grand-Place", "street": "Grand-Place 1", "city": "Brussels",
            "postal_code": "1000", "country": "Belgium", "latitude": 50.8467, "longitude": 4.3525}
ANTWERP = {**BRUSSELS, "name": "Antwerp Central", "street": "Koningin Astridplein 27",
           "city": "Antwerp", "postal_code": "2018", "latitude": 51.2172, "longitude": 4.4211}
PARIS = {**BRUSSELS, "name": "Eiffel Tower", "street": "Champ de Mars", "city": "Paris",
         "postal_code": "75007", "country": "France", "latitude": 48.8584, "longitude": 2.2945}


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_crud_flow(client):
    created = client.post("/addresses", json=BRUSSELS)
    assert created.status_code == 201
    address_id = created.json()["id"]

    assert client.get(f"/addresses/{address_id}").json()["city"] == "Brussels"

    updated = client.patch(f"/addresses/{address_id}", json={"name": "Town Hall"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "Town Hall"
    assert updated.json()["city"] == "Brussels"  # untouched

    assert client.delete(f"/addresses/{address_id}").status_code == 204
    assert client.get(f"/addresses/{address_id}").status_code == 404


@pytest.mark.parametrize("bad", [
    {"latitude": 91}, {"longitude": -181}, {"name": "   "}, {"city": ""},
])
def test_validation_rejects_bad_input(client, bad):
    assert client.post("/addresses", json={**BRUSSELS, **bad}).status_code == 422


def test_missing_field_rejected(client):
    payload = {k: v for k, v in BRUSSELS.items() if k != "latitude"}
    assert client.post("/addresses", json=payload).status_code == 422


def test_nearby(client):
    for place in (BRUSSELS, ANTWERP, PARIS):
        client.post("/addresses", json=place)

    resp = client.get("/addresses/nearby",
                      params={"latitude": 50.8467, "longitude": 4.3525, "distance_km": 60})
    assert resp.status_code == 200
    names = [a["name"] for a in resp.json()]
    assert names == ["Grand-Place", "Antwerp Central"]  # nearest first, Paris excluded

    resp = client.get("/addresses/nearby",
                      params={"latitude": 50.8467, "longitude": 4.3525, "distance_km": 300})
    assert len(resp.json()) == 3


def test_nearby_rejects_invalid_radius(client):
    resp = client.get("/addresses/nearby",
                      params={"latitude": 0, "longitude": 0, "distance_km": -5})
    assert resp.status_code == 422


def test_nearby_across_antimeridian(client):
    client.post("/addresses", json={**BRUSSELS, "latitude": 0, "longitude": 179.9})
    resp = client.get("/addresses/nearby",
                      params={"latitude": 0, "longitude": -179.9, "distance_km": 50})
    assert len(resp.json()) == 1


def test_haversine_known_distance():
    # Brussels -> Paris is roughly 264 km
    assert 260 < haversine_km(50.8467, 4.3525, 48.8584, 2.2945) < 270
