"""Pydantic schemas used for request validation and response serialization."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# Reusable constrained types: whitespace is stripped and empty strings rejected.
NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Latitude = Annotated[float, Field(ge=-90, le=90, description="Latitude in decimal degrees")]
Longitude = Annotated[float, Field(ge=-180, le=180, description="Longitude in decimal degrees")]


class AddressBase(BaseModel):
    """Fields shared by create and read schemas."""

    name: Annotated[NonEmptyStr, Field(max_length=100, examples=["Head Office"])]
    street: Annotated[NonEmptyStr, Field(max_length=200, examples=["Grand-Place 1"])]
    city: Annotated[NonEmptyStr, Field(max_length=100, examples=["Brussels"])]
    postal_code: Annotated[NonEmptyStr, Field(max_length=20, examples=["1000"])]
    country: Annotated[NonEmptyStr, Field(max_length=100, examples=["Belgium"])]
    latitude: Annotated[Latitude, Field(examples=[50.8467])]
    longitude: Annotated[Longitude, Field(examples=[4.3525])]


class AddressCreate(AddressBase):
    """Payload for creating an address."""


class AddressUpdate(BaseModel):
    """Payload for a partial update: every field is optional."""

    name: Annotated[NonEmptyStr, Field(max_length=100)] | None = None
    street: Annotated[NonEmptyStr, Field(max_length=200)] | None = None
    city: Annotated[NonEmptyStr, Field(max_length=100)] | None = None
    postal_code: Annotated[NonEmptyStr, Field(max_length=20)] | None = None
    country: Annotated[NonEmptyStr, Field(max_length=100)] | None = None
    latitude: Latitude | None = None
    longitude: Longitude | None = None


class AddressRead(AddressBase):
    """Address as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class AddressWithDistance(AddressRead):
    """Address plus its distance from the searched point."""

    distance_km: float
