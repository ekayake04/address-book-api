"""Database operations for addresses (the data-access layer)."""

import logging

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.geo import bounding_box, haversine_km

logger = logging.getLogger(__name__)


def get_address(db: Session, address_id: int) -> models.Address | None:
    """Return one address by id, or None if it does not exist."""
    return db.get(models.Address, address_id)


def list_addresses(db: Session, skip: int = 0, limit: int = 100) -> list[models.Address]:
    """Return a page of addresses ordered by id."""
    stmt = select(models.Address).order_by(models.Address.id).offset(skip).limit(limit)
    return list(db.scalars(stmt))


def create_address(db: Session, data: schemas.AddressCreate) -> models.Address:
    """Insert a new address and return it."""
    address = models.Address(**data.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    logger.info("Created address id=%s", address.id)
    return address


def update_address(
    db: Session, address: models.Address, data: schemas.AddressUpdate
) -> models.Address:
    """Apply the fields that were sent in the request to an existing address."""
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(address, field, value)
    db.commit()
    db.refresh(address)
    logger.info("Updated address id=%s fields=%s", address.id, sorted(changes))
    return address


def delete_address(db: Session, address: models.Address) -> None:
    """Delete an address."""
    db.delete(address)
    db.commit()
    logger.info("Deleted address id=%s", address.id)


def find_nearby(
    db: Session, latitude: float, longitude: float, distance_km: float
) -> list[tuple[models.Address, float]]:
    """Return (address, distance_km) pairs within distance_km, nearest first.

    A cheap bounding-box query narrows the candidates in SQL; the exact
    haversine distance is then computed for each candidate.
    """
    min_lat, max_lat, min_lon, max_lon = bounding_box(latitude, longitude, distance_km)
    lon = models.Address.longitude

    # Handle boxes that cross the antimeridian (±180° longitude).
    if min_lon < -180:
        lon_filter = or_(lon >= min_lon + 360, lon <= max_lon)
    elif max_lon > 180:
        lon_filter = or_(lon >= min_lon, lon <= max_lon - 360)
    else:
        lon_filter = lon.between(min_lon, max_lon)

    stmt = select(models.Address).where(
        and_(models.Address.latitude.between(min_lat, max_lat), lon_filter)
    )
    candidates = db.scalars(stmt).all()

    results = []
    for address in candidates:
        distance = haversine_km(latitude, longitude, address.latitude, address.longitude)
        if distance <= distance_km:
            results.append((address, round(distance, 3)))
    results.sort(key=lambda pair: pair[1])

    logger.info(
        "Nearby search lat=%s lon=%s radius=%skm: %d candidates, %d matches",
        latitude, longitude, distance_km, len(candidates), len(results),
    )
    return results
