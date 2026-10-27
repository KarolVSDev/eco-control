from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EcoAutomationRequest(BaseModel):
    """Omitted, null and blank optional values leave stored data intact."""

    model_config = ConfigDict(extra="forbid")

    eco: str = Field(min_length=1)
    obu: str | None = None
    change_reason: str | None = None
    eco_type: str | None = None
    az_eco_register_date: date | None = None
    auto_ecr: Literal["YES", "NO"] | None = None
    change_bom: Literal["YES", "NO"] | None = None
    title: str | None = None

    @field_validator("*", mode="before")
    @classmethod
    def normalize_input(cls, value, info):
        if isinstance(value, str):
            value = value.strip()
            if not value and info.field_name != "eco":
                return None
        return value


class EcoAutomationResponse(BaseModel):
    status: Literal["updated", "unchanged"]
    eco_id: str
    eco: str
    changed_fields: list[str]
