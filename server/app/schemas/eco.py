from datetime import date, datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class EcoBase(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    # ----------------------------------------
    # IDENTIFICAÇÃO
    # ----------------------------------------
    product: str | None = None
    obu: str | None = None

    # ----------------------------------------
    # CLASSIFICAÇÃO
    # ----------------------------------------
    group: str | None = None
    owner: str | None = None
    item_type: str | None = None
    eco_type: str | None = None
    change_bom: str | None = None
    status: str | None = None
    receb: str | None = None

    # ----------------------------------------
    # ECO HQ
    # ----------------------------------------
    eco: str | None = None
    change_reason: str | None = None
    hq_eco_release_date: date | None = None
    az_eco_register_date: date | None = None
    auto_ecr: str | None = None
    council_meeting_week: str | None = None

    # ----------------------------------------
    # ORIGEM
    # ----------------------------------------
    hz_in_kr_eco_1: str | None = None
    hz_sh_in_receive_date_1: date | None = None

    hz_in_kr_eco_2: str | None = None
    hz_sh_in_receive_date_2: date | None = None

    hz_in_kr_eco_3: str | None = None
    hz_sh_in_receive_date_3: date | None = None

    # ----------------------------------------
    # AZ ECO
    # ----------------------------------------
    az_eco_no: str | None = None
    change_reason2: str | None = None
    change_bom_az: str | None = None
    az_eco_creation_date: date | None = None

    # ----------------------------------------
    # AGREEMENT OTHER DEPTS
    # ----------------------------------------
    agreement_start_1: date | None = None
    agreement_finish_1: date | None = None

    agreement_start_2: date | None = None
    agreement_finish_2: date | None = None

    agreement_start_3: date | None = None
    agreement_finish_3: date | None = None

    # ----------------------------------------
    # R&D APPROVAL
    # ----------------------------------------
    second_aprov_rd: str | None = None

    second_aprov_rd_start_1: date | None = None
    second_aprov_rd_finish_1: date | None = None

    second_aprov_rd_start_2: date | None = None
    second_aprov_rd_finish_2: date | None = None

    # ----------------------------------------
    # ADICIONAIS
    # ----------------------------------------
    change_reason_az: str | None = None
    model_az: str | None = None
    new_model: str | None = None
    origem_approval: str | None = None
    event: str | None = None
    comments: str | None = None

    # ----------------------------------------
    # SET ECO
    # ----------------------------------------
    set_eco: str | None = None
    set_eco_register_date: date | None = None
    set_eco_release_date: date | None = None
    set_eco_change_reason: str | None = None
    set_eco_model: str | None = None


class EcoCreate(EcoBase):
    pass


class EcoUpdate(EcoBase):
    pass


class EcoOut(EcoBase):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: str

    # gerados pelo sistema
    item: int | None = None
    position: int | None = None
    month: str | None = None
    au: str | None = None

    # calculados
    gap: str | int | None = None

    delay_eco_register: int | None = None
    eco_registration_week: str | None = None

    eco_origem_1: int | None = None
    eco_origem_2: int | None = None
    eco_origem_3: int | None = None

    gap_start_az_eco: int | None = None
    contar_eco_emitida_1_dias: bool | None = None

    gap_agreement: int | None = None
    gap_agreement_1: int | None = None
    gap_agreement_2: int | None = None
    gap_agreement_3: int | None = None
    gap_total_agreement: int | None = None

    gap_2st_1: int | None = None
    gap_2st_2: int | None = None
    gap_total_2st: int | None = None

    eco_release_week: str | None = None
    az_gap: int | None = None

    contar_eco_7: bool | None = None
    contar_eco_10: bool | None = None
    contar_eco_14: bool | None = None

    total_gap: int | None = None
    release_month: str | None = None
    release_year: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    # temporário para não quebrar
    # o Angular atual.
    computed: dict[str, Any] = Field(
        default_factory=dict
    )