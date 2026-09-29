from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select, update

from app.models.entities import (
    Eco,
    EcoHistory,
    AnalystPermission,
    FieldPermission,
)

from app.repository.eco_repository import EcoRepository
from app.repository.history_repository import HistoryRepository
from app.repository.settings_repository import SettingsRepository

from app.utils.eco_calculations import (
    compute_eco_fields,
    normalize_text,
)


MONTHS = [
    "JAN",
    "FEB",
    "MAR",
    "APR",
    "MAY",
    "JUN",
    "JUL",
    "AUG",
    "SEP",
    "OCT",
    "NOV",
    "DEC",
]


LABELS = {
    "status": "STATUS",
    "group_name": "GROUP",
    "obu": "OBU",
    "au": "AU",
    "owner": "OWNER",
    "eco": "ECO",
    "comments": "COMMENTS",
}


class EcoService:

    def __init__(self, db, user):
        self.db = db
        self.user = user

        self.repo = EcoRepository(db)
        self.history = HistoryRepository(db)
        self.settings = SettingsRepository(db)


    # =========================================================
    # PERMISSÕES
    # =========================================================

    def _field_permissions(self):
        """
        Retorna as permissões por campo
        configuradas para o usuário atual.
        """

        permissions = self.db.scalars(
            select(FieldPermission).where(
                FieldPermission.user_email
                == self.user.email
            )
        ).all()

        return {
            (
                "group"
                if permission.field_key == "group_name"
                else permission.field_key
            ): permission
            for permission in permissions
        }


    def _filter_allowed(self, changes):
        """
        Valida os campos que o usuário
        está tentando alterar.

        Admin:
            pode alterar qualquer campo
            permitido pelo schema.

        Analista:
            somente campos que possuem
            can_edit=True.
        """

        if self.user.role == "admin":
            return changes


        permissions = (
            self._field_permissions()
        )


        allowed = {}

        denied = []


        for key, value in changes.items():

            external_key = (
                "group"
                if key == "group_name"
                else key
            )


            permission = permissions.get(
                external_key
            )


            if (
                permission
                and permission.can_edit
            ):

                allowed[key] = value

            else:

                denied.append(
                    external_key
                )


        if denied:

            denied_fields = ", ".join(
                sorted(
                    set(denied)
                )
            )

            raise HTTPException(
                status_code=403,
                detail=(
                    "Você não possui permissão "
                    "para editar os seguintes "
                    f"campos: {denied_fields}."
                ),
            )


        if not allowed:

            raise HTTPException(
                status_code=403,
                detail=(
                    "Nenhum dos campos enviados "
                    "pode ser editado por você."
                ),
            )


        return allowed


    def _can_create(self):
        """
        Verifica a permissão geral
        can_create_eco.
        """

        if self.user.role == "admin":
            return True


        permission = self.db.scalar(
            select(
                AnalystPermission
            ).where(
                AnalystPermission.user_email
                == self.user.email
            )
        )


        return bool(
            permission
            and permission.can_create_eco
        )


    # =========================================================
    # AUXILIARES DE HISTÓRICO
    # =========================================================

    def _history_field_key(
        self,
        key,
    ):

        if key == "group_name":
            return "group"

        return key


    def _history_field_label(
        self,
        key,
    ):

        if key in LABELS:
            return LABELS[key]


        return (
            self
            ._history_field_key(key)
            .replace("_", " ")
            .upper()
        )


    def _history_value(
        self,
        value,
    ):

        if value is None:
            return None


        if hasattr(
            value,
            "isoformat",
        ):
            return value.isoformat()


        return str(value)


    def _record_history_fields(
        self,
        eco,
        action,
        fields,
    ):

        for (
            key,
            (
                old_value,
                new_value,
            ),
        ) in fields.items():

            history_key = (
                self._history_field_key(
                    key
                )
            )


            self.history.add(
                EcoHistory(
                    eco_id=eco.id,
                    eco_code=eco.eco,
                    item=eco.item,
                    field_key=history_key,
                    field_label=(
                        self
                        ._history_field_label(
                            key
                        )
                    ),
                    old_value=(
                        self
                        ._history_value(
                            old_value
                        )
                    ),
                    new_value=(
                        self
                        ._history_value(
                            new_value
                        )
                    ),
                    user_email=(
                        self.user.email
                    ),
                    user_name=(
                        self.user.full_name
                    ),
                    action=action,
                )
            )


    # =========================================================
    # LISTAGEM
    # =========================================================

    def list(
        self,
        **kwargs,
    ):

        items, total = (
            self.repo.list(
                **kwargs
            )
        )


        serialized_items = [
            self.serialize(item)
            for item in items
        ]


        return (
            serialized_items,
            total,
        )


    # =========================================================
    # SERIALIZAÇÃO
    # =========================================================

    def serialize(
        self,
        eco,
    ):
        """
        Converte a entidade ECO para a resposta
        da API e aplica as permissões
        de visualização.
        """

        data = {
            column.name: getattr(
                eco,
                column.name,
            )
            for column
            in eco.__table__.columns
        }


        data["id"] = str(
            eco.id
        )


        # -----------------------------------------------------
        # group_name interno -> group externo
        # -----------------------------------------------------

        data["group"] = data.pop(
            "group_name",
            None,
        )


        # -----------------------------------------------------
        # CAMPOS CALCULADOS
        # -----------------------------------------------------

        computed = (
            compute_eco_fields(
                eco
            )
        )


        data.update(
            computed
        )


        # Mantido por compatibilidade
        # com partes antigas do Angular.

        data["computed"] = (
            computed
        )


        # -----------------------------------------------------
        # ADMIN
        # -----------------------------------------------------

        if self.user.role == "admin":

            return data


        # -----------------------------------------------------
        # ANALISTA
        # -----------------------------------------------------

        permissions = (
            self._field_permissions()
        )


        for (
            field_key,
            permission,
        ) in permissions.items():

            if (
                permission.can_view
                is False
            ):

                data.pop(
                    field_key,
                    None,
                )


        return data


    # =========================================================
    # CREATE NORMAL
    # =========================================================

    def create(
        self,
        payload,
    ):

        # -----------------------------------------------------
        # PERMISSÃO
        # -----------------------------------------------------

        if not self._can_create():

            raise HTTPException(
                status_code=403,
                detail=(
                    "Você não possui permissão "
                    "para criar novas ECOs."
                ),
            )


        # -----------------------------------------------------
        # PAYLOAD
        # -----------------------------------------------------

        raw_data = (
            payload.model_dump(
                exclude_unset=True,
                exclude_none=True,
            )
        )


        data = {
            key: normalize_text(
                value
            )
            for key, value
            in raw_data.items()
        }


        # -----------------------------------------------------
        # GROUP
        # -----------------------------------------------------

        group = data.pop(
            "group",
            None,
        )


        if group is not None:

            data["group_name"] = (
                group
            )


        # -----------------------------------------------------
        # PERMISSÕES POR CAMPO
        # -----------------------------------------------------

        if (
            self.user.role
            != "admin"
        ):

            data = (
                self._filter_allowed(
                    data
                )
            )


        group = data.pop(
            "group_name",
            None,
        )


        # -----------------------------------------------------
        # OBU -> AU
        # -----------------------------------------------------

        if data.get("obu"):

            data["au"] = (
                self.settings
                .au_for_obu(
                    data["obu"]
                )
            )


        # -----------------------------------------------------
        # OWNER -> GROUP
        # -----------------------------------------------------

        if (
            data.get("owner")
            and not group
        ):

            group = (
                self.settings
                .group_for_owner(
                    data["owner"]
                )
            )


        # -----------------------------------------------------
        # ITEM / POSITION
        # -----------------------------------------------------

        next_item = (
            self.repo.next_item()
        )


        next_position = (
            self.repo.next_position()
        )


        eco = Eco(
            **data,
            group_name=group,
            item=next_item,
            position=next_position,
            month=MONTHS[
                datetime.now().month - 1
            ],
        )


        self.repo.create(
            eco
        )


        # -----------------------------------------------------
        # HISTÓRICO
        # -----------------------------------------------------

        created_fields = {}


        for submitted_key in raw_data:

            field_key = (
                "group_name"
                if submitted_key == "group"
                else submitted_key
            )


            value = getattr(
                eco,
                field_key,
                None,
            )


            if value is not None:

                created_fields[
                    field_key
                ] = (
                    None,
                    value,
                )


        if not created_fields:

            created_fields["eco"] = (
                None,
                eco.eco,
            )


        self._record_history_fields(
            eco,
            "created",
            created_fields,
        )


        self.db.commit()


        return self.serialize(
            eco
        )


    # =========================================================
    # CREATE ABAIXO DE UMA ECO
    # =========================================================

    def create_after(
        self,
        eco_id,
    ):
        """
        Cria uma ECO vazia imediatamente abaixo
        da ECO selecionada.

        ITEM:
            novo identificador permanente.

        POSITION:
            responsável pela posição visual.

        Exemplo:

        Antes:
            ITEM 90 -> position 100
            ITEM 88 -> position 99
            ITEM 72 -> position 98

        Criando abaixo do ITEM 88:

            ITEM 90 -> position 101
            ITEM 88 -> position 100
            NOVO    -> position 99
            ITEM 72 -> position 98
        """

        # -----------------------------------------------------
        # PERMISSÃO
        # -----------------------------------------------------

        if not self._can_create():

            raise HTTPException(
                status_code=403,
                detail=(
                    "Você não possui permissão "
                    "para criar novas ECOs."
                ),
            )


        # -----------------------------------------------------
        # ECO DE REFERÊNCIA
        # -----------------------------------------------------

        reference_eco = (
            self.repo.get(
                eco_id
            )
        )


        if not reference_eco:

            raise HTTPException(
                status_code=404,
                detail=(
                    "ECO de referência "
                    "não encontrada."
                ),
            )


        if (
            reference_eco.position
            is None
        ):

            raise HTTPException(
                status_code=409,
                detail=(
                    "A ECO selecionada não possui "
                    "posição válida para inserção."
                ),
            )


        # Guarda a posição ANTES de deslocar
        # as outras ECOs.

        insertion_position = (
            reference_eco.position
        )


        # -----------------------------------------------------
        # HISTÓRICO DAS POSIÇÕES DESLOCADAS
        # -----------------------------------------------------

        shifted_ecos = (
            self.db.scalars(
                select(Eco).where(
                    Eco.position
                    >= insertion_position
                )
            )
            .all()
        )


        for shifted_eco in shifted_ecos:

            old_position = (
                shifted_eco.position
            )


            if old_position is None:
                continue


            self._record_history_fields(
                shifted_eco,
                "updated",
                {
                    "position": (
                        old_position,
                        old_position + 1,
                    )
                },
            )


        # -----------------------------------------------------
        # ABRIR ESPAÇO NA ORDENAÇÃO
        # -----------------------------------------------------

        self.repo.make_space_at_position(
            insertion_position
        )


        # -----------------------------------------------------
        # NOVO ITEM
        # -----------------------------------------------------

        next_item = (
            self.repo.next_item()
        )


        # -----------------------------------------------------
        # CRIAR NOVA ECO
        # -----------------------------------------------------

        new_eco = Eco(

            item=next_item,

            position=(
                insertion_position
            ),

            month=MONTHS[
                datetime.now().month - 1
            ],

            item_type="MEC",

            eco_type="REGULAR",

            status="WORKING",
        )


        self.repo.create(
            new_eco
        )


        # -----------------------------------------------------
        # HISTÓRICO DA CRIAÇÃO
        # -----------------------------------------------------

        self._record_history_fields(
            new_eco,
            "created",
            {
                "item": (
                    None,
                    new_eco.item,
                ),
                "position": (
                    None,
                    new_eco.position,
                ),
                "month": (
                    None,
                    new_eco.month,
                ),
                "item_type": (
                    None,
                    new_eco.item_type,
                ),
                "eco_type": (
                    None,
                    new_eco.eco_type,
                ),
                "status": (
                    None,
                    new_eco.status,
                ),
            },
        )


        # -----------------------------------------------------
        # COMMIT
        # -----------------------------------------------------

        try:

            self.db.commit()

        except Exception:

            self.db.rollback()

            raise


        # -----------------------------------------------------
        # REFRESH
        # -----------------------------------------------------

        self.db.refresh(
            new_eco
        )


        return self.serialize(
            new_eco
        )


    # =========================================================
    # UPDATE
    # =========================================================

    def update(
        self,
        id,
        payload,
    ):

        eco = self.repo.get(
            id
        )


        if not eco:

            raise HTTPException(
                status_code=404,
                detail=(
                    "ECO não encontrada"
                ),
            )


        # -----------------------------------------------------
        # SOMENTE CAMPOS ENVIADOS
        # -----------------------------------------------------

        raw_changes = (
            payload.model_dump(
                exclude_unset=True
            )
        )


        changes = {
            key: normalize_text(
                value
            )
            for key, value
            in raw_changes.items()
        }


        # -----------------------------------------------------
        # GROUP EXTERNO -> INTERNO
        # -----------------------------------------------------

        if "group" in changes:

            changes[
                "group_name"
            ] = changes.pop(
                "group"
            )


        # -----------------------------------------------------
        # PERMISSÕES
        # -----------------------------------------------------

        changes = (
            self._filter_allowed(
                changes
            )
        )


        # -----------------------------------------------------
        # OBU -> AU
        # -----------------------------------------------------

        if changes.get("obu"):

            changes["au"] = (
                self.settings
                .au_for_obu(
                    changes["obu"]
                )
            )


        # -----------------------------------------------------
        # OWNER -> GROUP
        # -----------------------------------------------------

        if (
            changes.get("owner")
            and "group_name"
            not in changes
        ):

            mapped_group = (
                self.settings
                .group_for_owner(
                    changes["owner"]
                )
            )


            if mapped_group:

                changes["group_name"] = (
                    mapped_group
                )


        # -----------------------------------------------------
        # ALTERAÇÕES + HISTÓRICO
        # -----------------------------------------------------

        updated_fields = {}


        for (
            key,
            value,
        ) in changes.items():

            old_value = getattr(
                eco,
                key,
            )


            if (
                old_value
                == value
            ):

                continue


            setattr(
                eco,
                key,
                value,
            )


            updated_fields[key] = (
                old_value,
                value,
            )


        self._record_history_fields(
            eco,
            "updated",
            updated_fields,
        )


        self.db.commit()


        return self.serialize(
            eco
        )


    # =========================================================
    # DELETE
    # =========================================================

    def delete(
        self,
        id,
    ):

        # -----------------------------------------------------
        # SOMENTE ADMIN
        # -----------------------------------------------------

        if (
            self.user.role
            != "admin"
        ):

            raise HTTPException(
                status_code=403,
                detail=(
                    "Somente administradores "
                    "podem excluir ECOs."
                ),
            )


        eco = self.repo.get(
            id
        )


        if not eco:

            raise HTTPException(
                status_code=404,
                detail=(
                    "ECO não encontrada"
                ),
            )


        deleted_position = (
            eco.position
        )


        # -----------------------------------------------------
        # HISTÓRICO DA EXCLUSÃO
        # -----------------------------------------------------

        deleted_fields = {

            column.name: (
                getattr(
                    eco,
                    column.name,
                ),
                None,
            )

            for column
            in eco.__table__.columns

            if (
                column.name
                not in {
                    "id",
                    "created_at",
                    "updated_at",
                }

                and

                getattr(
                    eco,
                    column.name,
                )
                is not None
            )
        }


        self._record_history_fields(
            eco,
            "deleted",
            deleted_fields,
        )


        # -----------------------------------------------------
        # REGISTRAR MUDANÇA DAS POSIÇÕES
        # -----------------------------------------------------

        if (
            deleted_position
            is not None
        ):

            shifted_ecos = (
                self.db.scalars(
                    select(Eco).where(
                        Eco.position
                        > deleted_position
                    )
                )
                .all()
            )


            for shifted_eco in shifted_ecos:

                if (
                    shifted_eco.position
                    is None
                ):
                    continue


                self._record_history_fields(
                    shifted_eco,
                    "updated",
                    {
                        "position": (
                            shifted_eco.position,
                            shifted_eco.position - 1,
                        )
                    },
                )


        # -----------------------------------------------------
        # DELETE
        # -----------------------------------------------------

        self.repo.delete(
            eco
        )


        self.db.flush()


        # -----------------------------------------------------
        # REORGANIZAR POSITION
        # -----------------------------------------------------

        if (
            deleted_position
            is not None
        ):

            self.db.execute(
                update(Eco)
                .where(
                    Eco.position
                    > deleted_position
                )
                .values(
                    position=(
                        Eco.position - 1
                    )
                )
            )


        self.db.commit()