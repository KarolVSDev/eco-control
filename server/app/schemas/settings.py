from pydantic import (
    BaseModel,
    Field,
)


class ObuAuPayload(BaseModel):

    obu: str = Field(
        min_length=1,
        max_length=30,
    )

    au: str = Field(
        min_length=1,
        max_length=30,
    )


class OwnerGroupPayload(BaseModel):

    owner: str = Field(
        min_length=1,
        max_length=255,
    )

    group: str = Field(
        min_length=1,
        max_length=30,
    )


class ManagerPayload(BaseModel):

    name: str = Field(
        min_length=1,
        max_length=255,
    )