from sqlalchemy import select

from app.models.entities import (
    Manager,
    ObuAuMapping,
    OwnerGroupMapping,
)


class SettingsRepository:

    def __init__(
        self,
        db,
    ):
        self.db = db


    # =========================================================
    # CONSULTAS UTILIZADAS PELO ECO
    # =========================================================

    def au_for_obu(
        self,
        obu,
    ):
        item = self.db.scalar(
            select(
                ObuAuMapping
            ).where(
                ObuAuMapping.obu == obu
            )
        )

        return (
            item.au
            if item
            else None
        )


    def group_for_owner(
        self,
        owner,
    ):
        item = self.db.scalar(
            select(
                OwnerGroupMapping
            ).where(
                OwnerGroupMapping.owner == owner
            )
        )

        return (
            item.group_name
            if item
            else None
        )


    # =========================================================
    # LISTAGEM
    # =========================================================

    def all_obu_au(
        self,
    ):
        return (
            self.db.scalars(
                select(
                    ObuAuMapping
                ).order_by(
                    ObuAuMapping.obu
                )
            )
            .all()
        )


    def all_owner_group(
        self,
    ):
        return (
            self.db.scalars(
                select(
                    OwnerGroupMapping
                ).order_by(
                    OwnerGroupMapping.owner
                )
            )
            .all()
        )


    def all_managers(
        self,
    ):
        return (
            self.db.scalars(
                select(
                    Manager
                ).order_by(
                    Manager.name
                )
            )
            .all()
        )


    # =========================================================
    # OBU → AU
    # =========================================================

    def get_obu_au(
        self,
        mapping_id,
    ):
        return self.db.get(
            ObuAuMapping,
            mapping_id,
        )


    def get_obu_au_by_obu(
        self,
        obu,
    ):
        return self.db.scalar(
            select(
                ObuAuMapping
            ).where(
                ObuAuMapping.obu == obu
            )
        )


    def create_obu_au(
        self,
        item,
    ):
        self.db.add(
            item
        )

        self.db.flush()

        return item


    def delete_obu_au(
        self,
        item,
    ):
        self.db.delete(
            item
        )


    # =========================================================
    # OWNER → GROUP
    # =========================================================

    def get_owner_group(
        self,
        mapping_id,
    ):
        return self.db.get(
            OwnerGroupMapping,
            mapping_id,
        )


    def get_owner_group_by_owner(
        self,
        owner,
    ):
        return self.db.scalar(
            select(
                OwnerGroupMapping
            ).where(
                OwnerGroupMapping.owner == owner
            )
        )


    def create_owner_group(
        self,
        item,
    ):
        self.db.add(
            item
        )

        self.db.flush()

        return item


    def delete_owner_group(
        self,
        item,
    ):
        self.db.delete(
            item
        )


    # =========================================================
    # MANAGERS
    # =========================================================

    def get_manager(
        self,
        manager_id,
    ):
        return self.db.get(
            Manager,
            manager_id,
        )


    def get_manager_by_name(
        self,
        name,
    ):
        return self.db.scalar(
            select(
                Manager
            ).where(
                Manager.name == name
            )
        )


    def create_manager(
        self,
        manager,
    ):
        self.db.add(
            manager
        )

        self.db.flush()

        return manager


    def delete_manager(
        self,
        manager,
    ):
        self.db.delete(
            manager
        )