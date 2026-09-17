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
            permission.field_key: permission
            for permission in permissions
        }

    def _filter_allowed(self, changes):
        """
        Valida campos que o usuário está tentando alterar.

        Admin:
            pode alterar qualquer campo permitido
            pelo schema.

        Analyst:
            somente campos com can_edit=True.

        Se a requisição tentar alterar ao menos
        um campo não autorizado, toda a operação
        é rejeitada.
        """

        if self.user.role == "admin":
            return changes

        permissions = self._field_permissions()

        allowed = {}
        denied = []

        for key, value in changes.items():

            # Banco usa group_name,
            # mas a permissão usa "group".
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

        # Segurança:
        # não ignoramos silenciosamente
        # campos não autorizados.
        if denied:
            denied_fields = ", ".join(
                sorted(set(denied))
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
    # AUXILIARES
    # =========================================================

    def _history_field_key(self, key):
        """
        Converte nomes internos do banco
        para o nome utilizado externamente.
        """

        if key == "group_name":
            return "group"

        return key

    def _history_field_label(self, key):
        """
        Retorna um label amigável
        para o histórico.
        """

        if key in LABELS:
            return LABELS[key]

        return (
            self._history_field_key(key)
            .replace("_", " ")
            .upper()
        )

    # =========================================================
    # LISTAGEM
    # =========================================================

    def list(self, **kwargs):
        items, total = self.repo.list(
            **kwargs
        )

        serialized_items = [
            self.serialize(item)
            for item in items
        ]

        return serialized_items, total

    # =========================================================
    # SERIALIZAÇÃO
    # =========================================================

    def serialize(self, e):
        """
        Converte a entidade Eco para resposta
        da API e aplica permissões de visualização.
        """

        data = {
            column.name: getattr(
                e,
                column.name,
            )
            for column
            in e.__table__.columns
        }

        data["id"] = str(e.id)

        # O banco utiliza group_name,
        # mas o frontend utiliza group.
        data["group"] = data.pop(
            "group_name",
            None,
        )

        # =====================================================
        # CAMPOS CALCULADOS
        # =====================================================

        computed = compute_eco_fields(e)

        # Disponibiliza os calculados
        # diretamente no objeto.
        data.update(computed)

        # Mantido temporariamente para
        # compatibilidade com partes antigas.
        data["computed"] = computed

        # =====================================================
        # ADMIN
        # =====================================================

        if self.user.role == "admin":
            return data

        # =====================================================
        # ANALISTA
        # =====================================================

        permissions = (
            self._field_permissions()
        )

        # Só removemos campos que possuem
        # can_view explicitamente False.
        #
        # Campos sem configuração permanecem
        # visíveis, mantendo o mesmo comportamento
        # usado atualmente no Angular.
        for (
            field_key,
            permission,
        ) in permissions.items():

            if permission.can_view is False:
                data.pop(
                    field_key,
                    None,
                )

        # IMPORTANTE:
        # este return precisa ficar FORA do for.
        return data

    # =========================================================
    # CREATE
    # =========================================================

    def create(self, payload):

        # -----------------------------------------------------
        # Permissão geral
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
        # Payload
        # -----------------------------------------------------

        raw_data = payload.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        data = {
            key: normalize_text(value)
            for key, value
            in raw_data.items()
        }

        # group externo -> group_name interno
        group = data.pop(
            "group",
            None,
        )

        if group is not None:
            data["group_name"] = group

        # -----------------------------------------------------
        # Permissões por campo
        # -----------------------------------------------------

        if self.user.role != "admin":
            data = self._filter_allowed(
                data
            )

        # Retiramos novamente o group_name
        # para tratar abaixo.
        group = data.pop(
            "group_name",
            None,
        )

        # -----------------------------------------------------
        # OBU -> AU
        # -----------------------------------------------------

        if data.get("obu"):
            data["au"] = (
                self.settings.au_for_obu(
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
        # ITEM
        # -----------------------------------------------------

        next_item = (
            self.repo.next_item()
        )

        eco = Eco(
            **data,
            group_name=group,
            item=next_item,
            position=next_item,
            month=MONTHS[
                datetime.now().month - 1
            ],
        )

        self.repo.create(eco)

        # -----------------------------------------------------
        # AUDITORIA
        # -----------------------------------------------------

        self.history.add(
            EcoHistory(
                eco_id=eco.id,
                eco_code=eco.eco,
                item=eco.item,
                field_key="eco",
                field_label="ECO criada",
                new_value=eco.eco,
                user_email=self.user.email,
                user_name=self.user.full_name,
                action="created",
            )
        )

        self.db.commit()

        return self.serialize(eco)

    # =========================================================
    # UPDATE
    # =========================================================

    def update(
        self,
        id,
        payload,
    ):

        eco = self.repo.get(id)

        if not eco:
            raise HTTPException(
                status_code=404,
                detail="ECO não encontrada",
            )

        # -----------------------------------------------------
        # Somente campos enviados
        # -----------------------------------------------------

        raw_changes = (
            payload.model_dump(
                exclude_unset=True
            )
        )

        changes = {
            key: normalize_text(value)
            for key, value
            in raw_changes.items()
        }

        # Front/API -> banco
        if "group" in changes:
            changes["group_name"] = (
                changes.pop("group")
            )

        # -----------------------------------------------------
        # Permissões
        # -----------------------------------------------------

        changes = self._filter_allowed(
            changes
        )

        # -----------------------------------------------------
        # OBU -> AU
        # -----------------------------------------------------

        if changes.get("obu"):

            changes["au"] = (
                self.settings.au_for_obu(
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

        for key, value in changes.items():

            old_value = getattr(
                eco,
                key,
            )

            if old_value == value:
                continue

            setattr(
                eco,
                key,
                value,
            )

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
                        self._history_field_label(
                            key
                        )
                    ),

                    old_value=str(
                        old_value
                        if old_value is not None
                        else ""
                    ),

                    new_value=str(
                        value
                        if value is not None
                        else ""
                    ),

                    user_email=(
                        self.user.email
                    ),

                    user_name=(
                        self.user.full_name
                    ),

                    action="updated",
                )
            )

        self.db.commit()

        return self.serialize(eco)

    # =========================================================
    # DELETE
    # =========================================================

    def delete(self, id):

        # Exclusão exclusiva para admin.
        if self.user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail=(
                    "Somente administradores "
                    "podem excluir ECOs."
                ),
            )

        eco = self.repo.get(id)

        if not eco:
            raise HTTPException(
                status_code=404,
                detail="ECO não encontrada",
            )

        deleted_item = (
            eco.item or 0
        )

        # -----------------------------------------------------
        # AUDITORIA
        # -----------------------------------------------------

        self.history.add(
            EcoHistory(
                eco_id=eco.id,
                eco_code=eco.eco,
                item=eco.item,

                field_key="eco",
                field_label="ECO excluída",

                old_value=eco.eco,

                user_email=(
                    self.user.email
                ),

                user_name=(
                    self.user.full_name
                ),

                action="deleted",
            )
        )

        # -----------------------------------------------------
        # DELETE
        # -----------------------------------------------------

        self.repo.delete(eco)

        self.db.flush()

        # Mantém a sequência ITEM
        # utilizada atualmente pelo sistema.
        if deleted_item:

            self.db.execute(
                update(Eco)
                .where(
                    Eco.item
                    > deleted_item
                )
                .values(
                    item=Eco.item - 1
                )
            )

        self.db.commit()