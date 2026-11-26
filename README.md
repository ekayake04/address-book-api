# Address Book API

A minimal address book REST API built with **FastAPI**, **SQLAlchemy 2.0** and **SQLite**.
API users can create, read, update and delete addresses (with coordinates) and retrieve
all addresses within a given distance of a location.

---

## Quick start

**Requirements:** Python **3.10 or newer** and `git`.

```bash
# 1. Clone the repository
git clone https://github.com/ekayake04/address-book-api.git
cd address-book-api

# 2. Create and activate a virtual environment (Python 3.10+)
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the tests
pytest -v

# 5. Start the API
uvicorn app.main:app --reload
```

Then open **http://127.0.0.1:8000/docs** for the interactive Swagger UI.
The SQLite database file `addresses.db` is created automatically on first start.

### ⚠️ Note for macOS users: check your Python version

macOS ships with **Python 3.9** as the default `python3`, which is too old for this
project (you would see `TypeError: unsupported operand type(s) for |`). Check first:

```bash
python3 --version
```

If it prints 3.9 or lower, create the virtual environment with a newer interpreter
instead, for example:

```bash
python3.12 -m venv .venv           # or python3.11 / python3.13
```

If no newer Python is installed (or Homebrew's Python fails while creating the venv),
[`uv`](https://docs.astral.sh/uv/) is the quickest alternative. It downloads its own
standalone Python:

```bash
brew install uv                    # or: curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

---

## Trying it out in Swagger (http://127.0.0.1:8000/docs)

1. **POST `/addresses`**: click *Try it out* and send, for example:
   ```json
   {"name": "Grand-Place", "street": "Grand-Place 1", "city": "Brussels",
    "postal_code": "1000", "country": "Belgium", "latitude": 50.8467, "longitude": 4.3525}
   ```
   Add a couple more (e.g. Antwerp `51.2172, 4.4211`, Paris `48.8584, 2.2945`).
2. **GET `/addresses/nearby`**: `latitude=50.85`, `longitude=4.35`, `distance_km=60`
   returns Brussels and Antwerp (nearest first) but not Paris.
3. **PATCH `/addresses/{id}`**: send only the fields to change, e.g. `{"name": "Town Hall"}`.
4. **DELETE `/addresses/{id}`**: returns `204`; a following GET returns `404`.
5. Try invalid input (e.g. `"latitude": 91` or an empty `"city"`) and you get a `422`
   with a clear validation message.

### Same thing with curl

```bash
curl -X POST http://127.0.0.1:8000/addresses \
  -H "Content-Type: application/json" \
  -d '{"name":"Grand-Place","street":"Grand-Place 1","city":"Brussels",
       "postal_code":"1000","country":"Belgium","latitude":50.8467,"longitude":4.3525}'

curl "http://127.0.0.1:8000/addresses/nearby?latitude=50.85&longitude=4.35&distance_km=10"
```

---

## API endpoints

| Method | Path                | Description                                                  |
|--------|---------------------|--------------------------------------------------------------|
| POST   | `/addresses`        | Create an address                                            |
| GET    | `/addresses`        | List addresses (`skip`, `limit` pagination)                  |
| GET    | `/addresses/{id}`   | Get one address                                              |
| PATCH  | `/addresses/{id}`   | Partially update an address                                  |
| DELETE | `/addresses/{id}`   | Delete an address                                            |
| GET    | `/addresses/nearby` | Addresses within `distance_km` of `latitude`/`longitude`, nearest first, each with its `distance_km` |
| GET    | `/health`           | Health check                                                 |

### Validation rules

| Field                                          | Rule                                        |
|------------------------------------------------|---------------------------------------------|
| `name`, `street`, `city`, `postal_code`, `country` | required, whitespace trimmed, not empty, max length (100/200/100/20/100) |
| `latitude`                                     | required, between −90 and 90                |
| `longitude`                                    | required, between −180 and 180              |
| `distance_km` (search)                         | greater than 0, at most 20,100 km (half Earth's circumference) |

---

## Logging

Logs go to stdout in the format `timestamp | level | logger | message`:

- every HTTP request: method, path, status code and duration (middleware in `app/main.py`)
- every create / update / delete, with the address id and changed fields
- every nearby search: parameters, number of candidates and matches
- `404` lookups as warnings; unhandled errors with full traceback

Example:
```
2026-11-26 10:15:02,113 | INFO     | app.crud | Created address id=1
2026-11-26 10:15:02,114 | INFO     | app.main | POST /addresses -> 201 (4.2 ms)
```

---

## Configuration (optional)

| Environment variable | Default                    | Purpose                    |
|----------------------|----------------------------|----------------------------|
| `DATABASE_URL`       | `sqlite:///./addresses.db` | Database location          |
| `LOG_LEVEL`          | `INFO`                     | `DEBUG`, `INFO`, `WARNING`, … |

Example: `LOG_LEVEL=DEBUG uvicorn app.main:app --reload`

---

## Project structure

```
app/
├── main.py            # FastAPI app, startup (table creation), request-logging middleware
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
└── test_api.py        # API tests on an isolated in-memory database
```

## Design notes

- **Layering:** routers handle HTTP, `crud.py` handles the database, `geo.py` holds pure
  math, so each part can be tested and changed on its own.
- **Distance search:** SQLite has no built-in geo functions, so the query first narrows
  rows with a latitude/longitude bounding box (indexed columns), then computes exact
  Haversine distances in Python. Searches that cross the ±180° antimeridian are handled.
  For large datasets, PostGIS or SpatiaLite would be the next step.
- **Tests:** each test uses a fresh in-memory SQLite database via FastAPI dependency
  overrides, so tests never touch `addresses.db`.
- **Schema creation:** tables are created on startup for simplicity; a production project
  would use Alembic migrations.
