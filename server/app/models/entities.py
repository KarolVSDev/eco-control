import uuid
from sqlalchemy import String, Integer, Boolean, Date, DateTime, Text, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Eco(Base):
    __tablename__ = "ecos"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    position: Mapped[int | None] = mapped_column(Integer)
    month: Mapped[str | None] = mapped_column(String(8), index=True)
    product: Mapped[str | None] = mapped_column(String(120))
    obu: Mapped[str | None] = mapped_column(String(30), index=True)
    au: Mapped[str | None] = mapped_column(String(30), index=True)
    group_name: Mapped[str | None] = mapped_column("group_name", String(30), index=True)
    owner: Mapped[str | None] = mapped_column(String(255), index=True)
    item_type: Mapped[str | None] = mapped_column(String(30))
    eco_type: Mapped[str | None] = mapped_column(String(120), index=True)
    change_bom: Mapped[str | None] = mapped_column(String(10))
    status: Mapped[str | None] = mapped_column(String(80), default="WORKING", index=True)
    receb: Mapped[str | None] = mapped_column(String(30))
    eco: Mapped[str | None] = mapped_column(String(80), index=True)
    change_reason: Mapped[str | None] = mapped_column(Text)
    hq_eco_release_date: Mapped[object | None] = mapped_column(Date)
    az_eco_register_date: Mapped[object | None] = mapped_column(Date)
    auto_ecr: Mapped[str | None] = mapped_column(String(10))
    council_meeting_week: Mapped[str | None] = mapped_column(String(40))
    hz_in_kr_eco_1: Mapped[str | None] = mapped_column(String(100))
    hz_sh_in_receive_date_1: Mapped[object | None] = mapped_column(Date)
    hz_in_kr_eco_2: Mapped[str | None] = mapped_column(String(100))
    hz_sh_in_receive_date_2: Mapped[object | None] = mapped_column(Date)
    hz_in_kr_eco_3: Mapped[str | None] = mapped_column(String(100))
    hz_sh_in_receive_date_3: Mapped[object | None] = mapped_column(Date)
    az_eco_no: Mapped[str | None] = mapped_column(String(100))
    change_reason2: Mapped[str | None] = mapped_column(Text)
    change_bom_az: Mapped[str | None] = mapped_column(String(10))
    az_eco_creation_date: Mapped[object | None] = mapped_column(Date)
    agreement_start_1: Mapped[object | None] = mapped_column(Date)
    agreement_finish_1: Mapped[object | None] = mapped_column(Date)
    agreement_start_2: Mapped[object | None] = mapped_column(Date)
    agreement_finish_2: Mapped[object | None] = mapped_column(Date)
    agreement_start_3: Mapped[object | None] = mapped_column(Date)
    agreement_finish_3: Mapped[object | None] = mapped_column(Date)
    second_aprov_rd: Mapped[str | None] = mapped_column(String(100))
    second_aprov_rd_start_1: Mapped[object | None] = mapped_column(Date)
    second_aprov_rd_finish_1: Mapped[object | None] = mapped_column(Date)
    second_aprov_rd_start_2: Mapped[object | None] = mapped_column(Date)
    second_aprov_rd_finish_2: Mapped[object | None] = mapped_column(Date)
    change_reason_az: Mapped[str | None] = mapped_column(Text)
    model_az: Mapped[str | None] = mapped_column(String(100))
    new_model: Mapped[str | None] = mapped_column(String(10))
    origem_approval: Mapped[str | None] = mapped_column(String(30))
    event: Mapped[str | None] = mapped_column(String(10))
    comments: Mapped[str | None] = mapped_column(Text)
    set_eco: Mapped[str | None] = mapped_column(String(100))
    set_eco_register_date: Mapped[object | None] = mapped_column(Date)
    set_eco_release_date: Mapped[object | None] = mapped_column(Date)
    set_eco_change_reason: Mapped[str | None] = mapped_column(Text)
    set_eco_model: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class EcoHistory(Base):
    __tablename__ = "eco_history"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    eco_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ecos.id", ondelete="SET NULL"), nullable=True, index=True)
    eco_code: Mapped[str | None] = mapped_column(String(100), index=True)
    item: Mapped[int | None] = mapped_column(Integer)
    field_key: Mapped[str] = mapped_column(String(100), index=True)
    field_label: Mapped[str | None] = mapped_column(String(160))
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    user_email: Mapped[str | None] = mapped_column(String(255), index=True)
    user_name: Mapped[str | None] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

class AnalystPermission(Base):
    __tablename__ = "analyst_permissions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_email: Mapped[str] = mapped_column(String(255), unique=True)
    can_create_eco: Mapped[bool] = mapped_column(Boolean, default=False)
    can_bulk_edit: Mapped[bool] = mapped_column(Boolean, default=False)
    can_view_history: Mapped[bool] = mapped_column(Boolean, default=True)

class FieldPermission(Base):
    __tablename__ = "field_permissions"
    __table_args__ = (UniqueConstraint("user_email", "field_key"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_email: Mapped[str] = mapped_column(String(255), index=True)
    field_key: Mapped[str] = mapped_column(String(100), index=True)
    can_view: Mapped[bool] = mapped_column(Boolean, default=True)
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False)

class ObuAuMapping(Base):
    __tablename__ = "obu_au_mappings"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    obu: Mapped[str] = mapped_column(String(30), unique=True)
    au: Mapped[str] = mapped_column(String(30))

class OwnerGroupMapping(Base):
    __tablename__ = "owner_group_mappings"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner: Mapped[str] = mapped_column(String(255), unique=True)
    group_name: Mapped[str] = mapped_column(String(30))

class Manager(Base):
    __tablename__ = "managers"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True)
