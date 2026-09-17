from pydantic import BaseModel


class GeneralPermissionUpdate(BaseModel):
    can_create_eco: bool = False
    can_bulk_edit: bool = False
    can_view_history: bool = True


class FieldPermissionUpdate(BaseModel):
    field_key: str
    can_view: bool = True
    can_edit: bool = False


class PermissionUpdate(BaseModel):
    general: GeneralPermissionUpdate
    fields: list[FieldPermissionUpdate]