"""HTTP endpoints for managing addresses."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/addresses", tags=["addresses"])

DbSession = Annotated[Session, Depends(get_db)]


def get_address_or_404(address_id: int, db: DbSession) -> models.Address:
    """Dependency that loads an address or raises 404."""
    address = crud.get_address(db, address_id)
    if address is None:
        logger.warning("Address id=%s not found", address_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Address not found")
    return address


ExistingAddress = Annotated[models.Address, Depends(get_address_or_404)]


@router.post("", response_model=schemas.AddressRead, status_code=status.HTTP_201_CREATED)
def create_address(payload: schemas.AddressCreate, db: DbSession):
    """Create a new address."""
    return crud.create_address(db, payload)


@router.get("", response_model=list[schemas.AddressRead])
def list_addresses(
    db: DbSession,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    """List addresses with simple pagination."""
    return crud.list_addresses(db, skip=skip, limit=limit)


# Declared before "/{address_id}" so "nearby" is not parsed as an id.
@router.get("/nearby", response_model=list[schemas.AddressWithDistance])
def find_nearby(
    db: DbSession,
    latitude: Annotated[float, Query(ge=-90, le=90, description="Latitude of the search point")],
    longitude: Annotated[float, Query(ge=-180, le=180, description="Longitude of the search point")],
    distance_km: Annotated[float, Query(gt=0, le=20_100, description="Search radius in km")],
):
    """Return addresses within `distance_km` of the given point, nearest first."""
    matches = crud.find_nearby(db, latitude, longitude, distance_km)
    return [
        schemas.AddressWithDistance(
            **schemas.AddressRead.model_validate(address).model_dump(), distance_km=distance
        )
        for address, distance in matches
    ]


@router.get("/{address_id}", response_model=schemas.AddressRead)
def read_address(address: ExistingAddress):
    """Get one address by id."""
    return address


@router.patch("/{address_id}", response_model=schemas.AddressRead)
def update_address(payload: schemas.AddressUpdate, address: ExistingAddress, db: DbSession):
    """Partially update an address; only the fields sent are changed."""
    return crud.update_address(db, address, payload)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address: ExistingAddress, db: DbSession) -> None:
    """Delete an address."""
    crud.delete_address(db, address)
