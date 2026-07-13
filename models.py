import re
from enum import Enum

from pydantic import BaseModel, Field, field_validator

ALERT_TYPE_CODE_PATTERN = re.compile(r"^[A-Z]{3}\d{3}$")


class Channel(str, Enum):
    EMAIL = "email"
    SMS = "sms"


class CampaignStatus(str, Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class GenerateRequest(BaseModel):
    alert_type_code: str
    brief: str = Field(min_length=10)
    channel: Channel

    @field_validator("alert_type_code")
    @classmethod
    def validate_alert_type_code(cls, value: str) -> str:
        if not ALERT_TYPE_CODE_PATTERN.fullmatch(value):
            raise ValueError(
                "alert_type_code must be 3 uppercase letters followed by 3 digits (e.g. ABC123)"
            )
        return value


class DraftResponse(BaseModel):
    campaign_id: int
    content: str
    status: CampaignStatus
    validation_notes: list[str] = []


class HealthResponse(BaseModel):
    status: str
