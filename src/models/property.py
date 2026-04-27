"""Pydantic models for Paraguayan property listings."""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class PropertyListing(BaseModel):
    """Standardized property listing model for all Paraguayan sources."""

    # Identity
    source: str = Field(description="Source site name (e.g., 'clasipar', 'infocasas')")
    source_url: str = Field(description="Original listing URL")
    external_id: Optional[str] = Field(None, description="ID from source site")

    # Core fields
    title: str = Field(description="Listing title")
    property_type: str = Field(
        description="Type: casa / departamento / terreno / local / penthouse / country / etc"
    )
    price: Optional[float] = Field(None, description="Price in PYG")
    price_usd: Optional[float] = Field(None, description="Price in USD if listed")
    currency: str = Field("PYG", description="Currency: PYG or USD")
    negotiable: bool = Field(False, description="Is price negotiable")

    # Location
    city: Optional[str] = Field(None, description="City (e.g., 'Asunción', 'Ciudad del Este')")
    district: Optional[str] = Field(None, description="District/neighborhood")
    address: Optional[str] = Field(None, description="Full address if available")
    zone: Optional[str] = Field(None, description="Zone description (e.g., 'Zona Norte')")
    coordinates: Optional[tuple[float, float]] = Field(None, description="(lat, lon) if available")

    # Property details
    bedrooms: Optional[int] = Field(None, ge=0)
    bathrooms: Optional[int] = Field(None, ge=0)
    total_area_m2: Optional[float] = Field(None, description="Total land area in m²")
    built_area_m2: Optional[float] = Field(None, description="Covered/built area in m²")
    floors: Optional[int] = Field(None, description="Number of floors")
    parking_spots: Optional[int] = Field(None, description="Garage/parking capacity")
    year_built: Optional[int] = Field(None, description="Construction year")

    # Description & media
    description: str = Field(default="", description="Full description text")
    features: list[str] = Field(default_factory=list, description="Amenities list")
    images: list[str] = Field(default_factory=list, description="Image URLs")
    video_url: Optional[str] = Field(None, description="Video tour URL if available")

    # Contact
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    agency: Optional[str] = Field(None, description="Real estate agency name")

    # Metadata
    listing_date: Optional[date] = Field(None, description="When the listing was posted")
    last_updated: Optional[date] = Field(None, description="When listing was last updated")
    scraped_at: datetime = Field(default_factory=datetime.now)
    status: str = Field("active", description="active / sold / rented / removed")


class SourceConfig(BaseModel):
    """Configuration for a single scraping source."""

    name: str
    display_name: str
    base_url: str
    search_urls: list[str]
    enabled: bool = True
    rate_limit_delay: float = 2.0  # seconds between requests
    requires_js: bool = False
    requires_auth: bool = False
    max_pages: int = 50
    respect_robots: bool = True
