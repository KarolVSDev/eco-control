from datetime import (
    date,
    datetime,
)

from fastapi import HTTPException
from sqlalchemy import select

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
    # FILTROS GENÉRICOS DE COLUNA
    # =========================================================

    @staticmethod
    def _normalize_filter_text(
        value,
    ) -> str:

        if value is None:
            return ""


        if isinstance(
            value,
            bool,
        ):
            return (
                "yes"
                if value
                else "no"
            )


        if isinstance(
            value,
            datetime,
        ):
            return (
                value
                .date()
                .isoformat()
                .casefold()
            )


        if isinstance(
            value,
            date,
        ):
            return (
                value
                .isoformat()
                .casefold()
            )


        return (
            " ".join(
                str(value)
                .split()
            )
            .casefold()
        )


    def _matches_column_filter(
        self,
        row: dict,
        column_key: str,
        expected,
    ) -> bool:

        # ---------------------------------------------
        # aliases externos
        # ---------------------------------------------

        key = (
            "group"
            if column_key
            == "group_name"
            else column_key
        )


        # ---------------------------------------------
        # campo não disponível
        #
        # Isso também respeita can_view:
        # se serialize() removeu o campo,
        # ele não pode ser usado para inferir dados.
        # ---------------------------------------------

        if key not in row:
            return False


        actual = row.get(
            key
        )


        expected_text = (
            self._normalize_filter_text(
                expected
            )
        )


        # ---------------------------------------------
        # sem filtro
        # ---------------------------------------------

        if not expected_text:
            return True


        # ---------------------------------------------
        # filtrar valores vazios
        # ---------------------------------------------

        if (
            expected_text
            == "__empty__"
        ):

            return (
                actual is None
                or
                self._normalize_filter_text(
                    actual
                )
                in {
                    "",
                    "-",
                }
            )


        # ---------------------------------------------
        # filtrar valores preenchidos
        # ---------------------------------------------

        if (
            expected_text
            == "__not_empty__"
        ):

            return not (
                actual is None
                or
                self._normalize_filter_text(
                    actual
                )
                in {
                    "",
                    "-",
                }
            )


        # ---------------------------------------------
        # boolean
        #
        # No Angular é exibido:
        # True  -> YES
        # False -> NO
        # ---------------------------------------------

        if isinstance(
            actual,
            bool,
        ):

            aliases = {
                True: {
                    "yes",
                    "true",
                    "1",
                    "sim",
                },

                False: {
                    "no",
                    "false",
                    "0",
                    "não",
                    "nao",
                },
            }


            return (
                expected_text
                in aliases[
                    actual
                ]
            )


        # ---------------------------------------------
        # números
        #
        # ITEM = 31 não deve casar com 310.
        # AZ GAP = 15 não deve casar com 115.
        # ---------------------------------------------

        if isinstance(
            actual,
            (
                int,
                float,
            ),
        ):

            return (
                self._normalize_filter_text(
                    actual
                )
                ==
                expected_text
            )


        # ---------------------------------------------
        # datas
        # ---------------------------------------------

        if isinstance(
            actual,
            (
                date,
                datetime,
            ),
        ):

            return (
                self._normalize_filter_text(
                    actual
                )
                ==
                expected_text
            )


        # ---------------------------------------------
        # texto
        #
        # OWNER = "Ana" encontra:
        # "Ana Souza"
        #
        # COMMENTS = "motor" encontra:
        # "Ajuste do motor realizado"
        # ---------------------------------------------

        actual_text = (
            self._normalize_filter_text(
                actual
            )
        )


        return (
            expected_text
            in actual_text
        )


    def _apply_column_filters(
        self,
        rows: list[dict],
        column_filters:
            dict[str, str]
            | None,
    ) -> list[dict]:

        if not column_filters:
            return rows


        active_filters = {

            key: value

            for (
                key,
                value,
            )
            in column_filters.items()

            if (
                key
                and
                value is not None
                and
                str(value).strip()
            )
        }


        if not active_filters:
            return rows


        filtered = []


        for row in rows:

            matches = all(

                self
                ._matches_column_filter(
                    row,
                    key,
                    value,
                )

                for (
                    key,
                    value,
                )
                in active_filters.items()
            )


            if matches:
                filtered.append(
                    row
                )


        return filtered
        # =========================================================
    # LISTAGEM
    # =========================================================

    def list(
        self,
        page=1,
        page_size=50,
        column_filters=None,
        **kwargs,
    ):

        # -----------------------------------------------------
        # SEM FILTROS GENÉRICOS
        #
        # Mantém a consulta otimizada no PostgreSQL.
        # -----------------------------------------------------

        if not column_filters:

            items, total = (
                self.repo.list(
                    page=page,
                    page_size=page_size,
                    **kwargs,
                )
            )


            serialized_items = [

                self.serialize(
                    item
                )

                for item
                in items
            ]


            return (
                serialized_items,
                total,
            )


        # -----------------------------------------------------
        # COM FILTROS DE QUALQUER COLUNA
        #
        # Precisamos calcular primeiro os campos derivados:
        #
        # GAP
        # AZ GAP
        # RELEASE MONTH
        # RELEASE YEAR
        # ECO WEEK
        # AGREEMENT...
        # -----------------------------------------------------

        items = (
            self.repo.list_all(
                **kwargs
            )
        )


        serialized_items = [

            self.serialize(
                item
            )

            for item
            in items
        ]


        # -----------------------------------------------------
        # APLICAR FILTROS
        # -----------------------------------------------------

        filtered_items = (
            self._apply_column_filters(
                serialized_items,
                column_filters,
            )
        )


        total = len(
            filtered_items
        )


        # -----------------------------------------------------
        # PAGINAÇÃO APÓS FILTRAR
        # -----------------------------------------------------

        start = (
            (
                page - 1
            )
            *
            page_size
        )


        end = (
            start
            +
            page_size
        )


        return (
            filtered_items[
                start:end
            ],
            total,
        )

        # =========================================================
    # LISTAGEM PARA EXPORTAÇÃO
    # =========================================================

    def list_for_export(
        self,
        column_filters=None,
        **kwargs,
    ):

        """
        Retorna todos os registros que correspondem
        aos filtros ativos.

        Não aplica paginação.

        A exportação XLSX deve utilizar este método
        para garantir que o Excel contenha exatamente
        os mesmos registros filtrados no ECO Control.
        """

        items = (
            self.repo.list_all(
                **kwargs
            )
        )


        serialized_items = [

            self.serialize(
                item
            )

            for item
            in items
        ]


        return (
            self._apply_column_filters(
                serialized_items,
                column_filters,
            )
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
        Cria uma nova ECO imediatamente abaixo
        da ECO selecionada.

        ITEM agora representa a sequência
        lógica das linhas.

        Exemplo:

        Antes:
            ITEM 7
            ITEM 8
            ITEM 9

        Criando abaixo do ITEM 7:

            ITEM 7
            ITEM 8  <- nova ECO
            ITEM 9  <- antiga ITEM 8
            ITEM 10 <- antiga ITEM 9

        POSITION continua sendo responsável
        pela ordem visual da tabela.
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


        # -----------------------------------------------------
        # VALIDAR ITEM
        # -----------------------------------------------------

        if (
            reference_eco.item
            is None
        ):

            raise HTTPException(
                status_code=409,
                detail=(
                    "A ECO selecionada não possui "
                    "ITEM válido para inserção."
                ),
            )


        # -----------------------------------------------------
        # VALIDAR POSITION
        # -----------------------------------------------------

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


        # -----------------------------------------------------
        # NOVO ITEM
        # -----------------------------------------------------

        new_item = (
            reference_eco.item
            + 1
        )


        # -----------------------------------------------------
        # NOVA POSITION
        # -----------------------------------------------------

        insertion_position = (
            reference_eco.position
        )


        # -----------------------------------------------------
        # ECOs QUE TERÃO ITEM ALTERADO
        # -----------------------------------------------------

        shifted_item_ecos = (
            self.db.scalars(
                select(Eco).where(
                    Eco.item
                    >= new_item
                )
            )
            .all()
        )


        # -----------------------------------------------------
        # ECOs QUE TERÃO POSITION ALTERADA
        # -----------------------------------------------------

        shifted_position_ecos = (
            self.db.scalars(
                select(Eco).where(
                    Eco.position
                    >= insertion_position
                )
            )
            .all()
        )


        # -----------------------------------------------------
        # HISTÓRICO DOS ITEMS DESLOCADOS
        # -----------------------------------------------------

        for shifted_eco in shifted_item_ecos:

            old_item = (
                shifted_eco.item
            )


            if old_item is None:
                continue


            self._record_history_fields(
                shifted_eco,
                "updated",
                {
                    "item": (
                        old_item,
                        old_item + 1,
                    )
                },
            )


        # -----------------------------------------------------
        # HISTÓRICO DAS POSIÇÕES DESLOCADAS
        # -----------------------------------------------------

        for shifted_eco in shifted_position_ecos:

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


        try:

            # -------------------------------------------------
            # ABRIR ESPAÇO NA SEQUÊNCIA DOS ITEMS
            # -------------------------------------------------

            self.repo.shift_items_up_from(
                new_item
            )


            # -------------------------------------------------
            # ABRIR ESPAÇO NA ORDENAÇÃO VISUAL
            # -------------------------------------------------

            self.repo.make_space_at_position(
                insertion_position
            )


            # -------------------------------------------------
            # CRIAR NOVA ECO
            # -------------------------------------------------

            new_eco = Eco(

                item=new_item,

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


            # -------------------------------------------------
            # HISTÓRICO DA NOVA ECO
            # -------------------------------------------------

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


            # -------------------------------------------------
            # COMMIT
            # -------------------------------------------------

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


        # -----------------------------------------------------
        # BUSCAR ECO
        # -----------------------------------------------------

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


        deleted_item = (
            eco.item
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
        # ECOs QUE TERÃO ITEM ALTERADO
        # -----------------------------------------------------

        shifted_item_ecos = []


        if (
            deleted_item
            is not None
        ):

            shifted_item_ecos = (
                self.db.scalars(
                    select(Eco).where(
                        Eco.item
                        > deleted_item
                    )
                )
                .all()
            )


        # -----------------------------------------------------
        # ECOs QUE TERÃO POSITION ALTERADA
        # -----------------------------------------------------

        shifted_position_ecos = []


        if (
            deleted_position
            is not None
        ):

            shifted_position_ecos = (
                self.db.scalars(
                    select(Eco).where(
                        Eco.position
                        > deleted_position
                    )
                )
                .all()
            )


        # -----------------------------------------------------
        # HISTÓRICO DOS ITEMS RENUMERADOS
        # -----------------------------------------------------

        for shifted_eco in shifted_item_ecos:

            old_item = (
                shifted_eco.item
            )


            if old_item is None:
                continue


            self._record_history_fields(
                shifted_eco,
                "updated",
                {
                    "item": (
                        old_item,
                        old_item - 1,
                    )
                },
            )


        # -----------------------------------------------------
        # HISTÓRICO DAS POSIÇÕES RENUMERADAS
        # -----------------------------------------------------

        for shifted_eco in shifted_position_ecos:

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
                        old_position - 1,
                    )
                },
            )


        try:

            # -------------------------------------------------
            # EXCLUIR ECO
            # -------------------------------------------------

            self.repo.delete(
                eco
            )


            # Necessário para liberar o ITEM
            # excluído antes da renumeração.

            self.db.flush()


            # -------------------------------------------------
            # FECHAR ESPAÇO NA SEQUÊNCIA DE ITEMS
            # -------------------------------------------------

            if (
                deleted_item
                is not None
            ):

                self.repo.shift_items_down_after(
                    deleted_item
                )


            # -------------------------------------------------
            # FECHAR ESPAÇO NA ORDENAÇÃO VISUAL
            # -------------------------------------------------

            if (
                deleted_position
                is not None
            ):

                self.repo.close_space_after_position(
                    deleted_position
                )


            # -------------------------------------------------
            # COMMIT
            # -------------------------------------------------

            self.db.commit()


        except Exception:

            self.db.rollback()

            raise