from fastapi import HTTPException

from app.models.entities import (
    Manager,
    ObuAuMapping,
    OwnerGroupMapping,
)

from app.repository.settings_repository import (
    SettingsRepository,
)


class SettingsService:

    def __init__(
        self,
        db,
    ):
        self.db = db

        self.repository = (
            SettingsRepository(
                db
            )
        )


    # =========================================================
    # OBU → AU
    # =========================================================

    def create_obu_au(
        self,
        payload,
    ):
        obu = (
            payload.obu
            .strip()
            .upper()
        )

        au = (
            payload.au
            .strip()
            .upper()
        )


        existing = (
            self.repository
            .get_obu_au_by_obu(
                obu
            )
        )


        if existing:

            raise HTTPException(
                status_code=409,
                detail=(
                    f"O OBU {obu} já possui "
                    "uma relação cadastrada."
                ),
            )


        item = ObuAuMapping(
            obu=obu,
            au=au,
        )


        self.repository.create_obu_au(
            item
        )

        self.db.commit()

        self.db.refresh(
            item
        )


        return self._obu_au_response(
            item
        )


    def update_obu_au(
        self,
        mapping_id,
        payload,
    ):
        item = (
            self.repository
            .get_obu_au(
                mapping_id
            )
        )


        if not item:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Relação OBU → AU "
                    "não encontrada."
                ),
            )


        obu = (
            payload.obu
            .strip()
            .upper()
        )

        au = (
            payload.au
            .strip()
            .upper()
        )


        existing = (
            self.repository
            .get_obu_au_by_obu(
                obu
            )
        )


        if (
            existing
            and existing.id != item.id
        ):

            raise HTTPException(
                status_code=409,
                detail=(
                    f"O OBU {obu} já possui "
                    "uma relação cadastrada."
                ),
            )


        item.obu = obu
        item.au = au


        self.db.commit()

        self.db.refresh(
            item
        )


        return self._obu_au_response(
            item
        )


    def delete_obu_au(
        self,
        mapping_id,
    ):
        item = (
            self.repository
            .get_obu_au(
                mapping_id
            )
        )


        if not item:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Relação OBU → AU "
                    "não encontrada."
                ),
            )


        self.repository.delete_obu_au(
            item
        )

        self.db.commit()


    # =========================================================
    # OWNER → GROUP
    # =========================================================

    def create_owner_group(
        self,
        payload,
    ):
        owner = (
            payload.owner
            .strip()
        )

        group = (
            payload.group
            .strip()
            .upper()
        )


        existing = (
            self.repository
            .get_owner_group_by_owner(
                owner
            )
        )


        if existing:

            raise HTTPException(
                status_code=409,
                detail=(
                    f"O owner {owner} já possui "
                    "um grupo cadastrado."
                ),
            )


        item = OwnerGroupMapping(
            owner=owner,
            group_name=group,
        )


        self.repository.create_owner_group(
            item
        )

        self.db.commit()

        self.db.refresh(
            item
        )


        return self._owner_group_response(
            item
        )


    def delete_owner_group(
        self,
        mapping_id,
    ):
        item = (
            self.repository
            .get_owner_group(
                mapping_id
            )
        )


        if not item:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Relação Owner → Group "
                    "não encontrada."
                ),
            )


        self.repository.delete_owner_group(
            item
        )

        self.db.commit()


    # =========================================================
    # GERENTES
    # =========================================================

    def create_manager(
        self,
        payload,
    ):
        name = (
            payload.name
            .strip()
        )


        existing = (
            self.repository
            .get_manager_by_name(
                name
            )
        )


        if existing:

            raise HTTPException(
                status_code=409,
                detail=(
                    "Este gerente já está "
                    "cadastrado."
                ),
            )


        manager = Manager(
            name=name
        )


        self.repository.create_manager(
            manager
        )

        self.db.commit()

        self.db.refresh(
            manager
        )


        return self._manager_response(
            manager
        )


    def delete_manager(
        self,
        manager_id,
    ):
        manager = (
            self.repository
            .get_manager(
                manager_id
            )
        )


        if not manager:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Gerente não encontrado."
                ),
            )


        self.repository.delete_manager(
            manager
        )

        self.db.commit()


    # =========================================================
    # SERIALIZAÇÃO
    # =========================================================

    def _obu_au_response(
        self,
        item,
    ):
        return {
            "id": str(item.id),
            "obu": item.obu,
            "au": item.au,
        }


    def _owner_group_response(
        self,
        item,
    ):
        return {
            "id": str(item.id),
            "owner": item.owner,
            "group": item.group_name,
        }


    def _manager_response(
        self,
        manager,
    ):
        return {
            "id": str(manager.id),
            "name": manager.name,
        }