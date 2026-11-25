# Address Book API

A minimal address book REST API built with **FastAPI**, **SQLAlchemy 2.0** and **SQLite**.
Users can create, read, update and delete addresses (with coordinates) and find all
addresses within a given distance of a point.

## Features

- CRUD endpoints for addresses
- Input validation with Pydantic v2 (required fields, non-empty strings, max lengths,
  latitude −90..90, longitude −180..180, positive search radius)
- Distance search using the Haversine formula, pre-filtered with an indexed
  bounding-box SQL query (also handles the ±180° antimeridian)
- Structured logging for every write and search
- Automated tests with an isolated in-memory database

## Project structure

```
app/
├── main.py            # FastAPI app, startup (table creation), router registration
├── config.py          # Settings from environment variables
├── logging_config.py  # Logging setup
├── database.py        # Engine, session factory, get_db dependency
├── models.py          # SQLAlchemy ORM model
├── schemas.py         # Pydantic request/response schemas (validation)
├── crud.py            # Data-access functions
├── geo.py             # Haversine distance + bounding box helpers
└── routers/
    └── addresses.py   # /addresses endpoints
tests/
└── test_api.py
```

## How to run

Requires Python 3.10+.

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/address-book-api.git
cd address-book-api

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the API
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/docs** for the interactive Swagger UI.
The SQLite file `addresses.db` is created automatically on first start.

### Run the tests

```bash
pytest -v
```

### Optional settings

| Variable       | Default                    |
|----------------|----------------------------|
| `DATABASE_URL` | `sqlite:///./addresses.db` |
| `LOG_LEVEL`    | `INFO`                     |

## API endpoints

| Method | Path                    | Description                                  |
|--------|-------------------------|----------------------------------------------|
| POST   | `/addresses`            | Create an address                            |
| GET    | `/addresses`            | List addresses (`skip`, `limit`)             |
| GET    | `/addresses/{id}`       | Get one address                              |
| PATCH  | `/addresses/{id}`       | Partially update an address                  |
| DELETE | `/addresses/{id}`       | Delete an address                            |
| GET    | `/addresses/nearby`     | Addresses within `distance_km` of `latitude`/`longitude`, nearest first |
| GET    | `/health`               | Health check                                 |

### Example

```bash
curl -X POST http://127.0.0.1:8000/addresses \
  -H "Content-Type: application/json" \
  -d '{"name":"Grand-Place","street":"Grand-Place 1","city":"Brussels",
       "postal_code":"1000","country":"Belgium","latitude":50.8467,"longitude":4.3525}'

curl "http://127.0.0.1:8000/addresses/nearby?latitude=50.85&longitude=4.35&distance_km=10"
```

## Design notes

- **Layering:** routers handle HTTP, `crud.py` handles the database, `geo.py` holds pure
  math, so each part can be tested and changed on its own.
- **Distance search:** SQLite has no built-in geo functions, so the query first narrows
  rows with a latitude/longitude bounding box (indexed columns), then computes exact
  Haversine distances in Python. For large datasets, PostGIS or SpatiaLite would be the
  next step.
- **Schema creation:** tables are created on startup for simplicity; a real project
  would use Alembic migrations.
