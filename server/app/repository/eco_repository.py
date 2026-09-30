from sqlalchemy import (
    func,
    or_,
    select,
    update,
)
from sqlalchemy.orm import Session

from app.models.entities import Eco


class EcoRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db


    # =========================================================
    # LISTAGEM
    # =========================================================

    def list(
        self,
        page=1,
        page_size=50,
        search=None,
        status=None,
        month=None,
        group=None,
        obu=None,
        item_type=None,
        eco_type=None,
    ):

        query = select(Eco)

        count_query = (
            select(func.count())
            .select_from(Eco)
        )

        filters = []


        # -----------------------------------------------------
        # BUSCA GERAL
        # -----------------------------------------------------

        if search:

            search_text = (
                f"%{search.strip()}%"
            )

            filters.append(
                or_(
                    Eco.eco.ilike(
                        search_text
                    ),
                    Eco.owner.ilike(
                        search_text
                    ),
                    Eco.product.ilike(
                        search_text
                    ),
                    Eco.comments.ilike(
                        search_text
                    ),
                )
            )


        # -----------------------------------------------------
        # FILTROS
        # -----------------------------------------------------

        if status:

            filters.append(
                Eco.status == status
            )


        if month:

            filters.append(
                Eco.month == month
            )


        if group:

            filters.append(
                Eco.group_name == group
            )


        if obu:

            filters.append(
                Eco.obu == obu
            )


        if item_type:

            filters.append(
                Eco.item_type == item_type
            )


        if eco_type:

            filters.append(
                Eco.eco_type == eco_type
            )


        # -----------------------------------------------------
        # APLICAR FILTROS
        # -----------------------------------------------------

        if filters:

            query = query.where(
                *filters
            )

            count_query = (
                count_query.where(
                    *filters
                )
            )


        # -----------------------------------------------------
        # TOTAL
        # -----------------------------------------------------

        total = (
            self.db.scalar(
                count_query
            )
            or 0
        )


        # -----------------------------------------------------
        # PAGINAÇÃO / ORDEM VISUAL
        # -----------------------------------------------------

        items = (
            self.db.scalars(
                query
                .order_by(
                    Eco.position.desc(),
                    Eco.item.desc(),
                )
                .offset(
                    (page - 1)
                    * page_size
                )
                .limit(
                    page_size
                )
            )
            .all()
        )


        return (
            items,
            total,
        )


    # =========================================================
    # BUSCAR ECO
    # =========================================================

    def get(
        self,
        id,
    ):

        return self.db.get(
            Eco,
            id,
        )


    # =========================================================
    # MAIOR ITEM ATUAL
    # =========================================================

    def max_item(
        self,
    ) -> int:

        return (
            self.db.scalar(
                select(
                    func.max(
                        Eco.item
                    )
                )
            )
            or 0
        )


    # =========================================================
    # PRÓXIMO ITEM
    # =========================================================

    def next_item(
        self,
    ) -> int:

        """
        Retorna o próximo ITEM considerando
        apenas as ECOs existentes atualmente.

        O histórico não participa mais desse
        cálculo porque ITEM agora representa
        uma sequência renumerável.
        """

        return (
            self.max_item()
            + 1
        )


    # =========================================================
    # DESLOCAR ITEMS PARA CIMA
    # =========================================================

    def shift_items_up_from(
        self,
        start_item: int,
    ) -> None:

        """
        Abre espaço para um novo ITEM.

        Exemplo:

        Antes:
            7
            8
            9

        shift_items_up_from(8)

        Depois:
            7
            9
            10

        Assim o ITEM 8 fica livre para
        receber a nova ECO.

        A atualização é feita em duas etapas
        porque Eco.item possui UNIQUE.
        """

        current_max = (
            self.max_item()
        )


        if (
            current_max
            < start_item
        ):

            return


        # Offset temporário maior que qualquer
        # ITEM atualmente existente.
        #
        # Exemplo:
        # max = 10
        # offset = 11
        #
        # 8  -> 19
        # 9  -> 20
        # 10 -> 21

        offset = (
            current_max + 1
        )


        # -----------------------------------------------------
        # ETAPA 1
        # mover para uma faixa temporária
        # -----------------------------------------------------

        self.db.execute(
            update(Eco)
            .where(
                Eco.item
                >= start_item
            )
            .values(
                item=(
                    Eco.item
                    + offset
                )
            )
        )


        # -----------------------------------------------------
        # ETAPA 2
        # trazer de volta acrescentando 1
        #
        # 19 -> 9
        # 20 -> 10
        # 21 -> 11
        # -----------------------------------------------------

        temporary_start = (
            start_item
            + offset
        )


        self.db.execute(
            update(Eco)
            .where(
                Eco.item
                >= temporary_start
            )
            .values(
                item=(
                    Eco.item
                    - offset
                    + 1
                )
            )
        )


    # =========================================================
    # DESLOCAR ITEMS PARA BAIXO
    # =========================================================

    def shift_items_down_after(
        self,
        deleted_item: int,
    ) -> None:

        """
        Fecha o espaço deixado após uma exclusão.

        Exemplo:

        Antes da exclusão:
            7
            8
            9
            10

        ITEM 8 é excluído.

        Depois:
            7
            8  <- antigo 9
            9  <- antigo 10

        IMPORTANTE:
        o registro excluído precisa ter sido
        removido e feito flush antes deste método.
        """

        current_max = (
            self.max_item()
        )


        if (
            current_max
            <= deleted_item
        ):

            return


        offset = (
            current_max + 1
        )


        first_item_to_shift = (
            deleted_item + 1
        )


        # -----------------------------------------------------
        # ETAPA 1
        # mover os ITEMs posteriores para
        # uma faixa temporária
        #
        # 9  -> 20
        # 10 -> 21
        # -----------------------------------------------------

        self.db.execute(
            update(Eco)
            .where(
                Eco.item
                > deleted_item
            )
            .values(
                item=(
                    Eco.item
                    + offset
                )
            )
        )


        # -----------------------------------------------------
        # ETAPA 2
        # trazer de volta diminuindo 1
        #
        # 20 -> 8
        # 21 -> 9
        # -----------------------------------------------------

        temporary_start = (
            first_item_to_shift
            + offset
        )


        self.db.execute(
            update(Eco)
            .where(
                Eco.item
                >= temporary_start
            )
            .values(
                item=(
                    Eco.item
                    - offset
                    - 1
                )
            )
        )


    # =========================================================
    # PRÓXIMA POSITION
    # =========================================================

    def next_position(
        self,
    ) -> int:

        current_max = (
            self.db.scalar(
                select(
                    func.max(
                        Eco.position
                    )
                )
            )
            or 0
        )


        return (
            current_max + 1
        )


    # =========================================================
    # ABRIR ESPAÇO NA ORDENAÇÃO
    # =========================================================

    def make_space_at_position(
        self,
        position: int,
    ) -> None:

        self.db.execute(
            update(Eco)
            .where(
                Eco.position
                >= position
            )
            .values(
                position=(
                    Eco.position + 1
                )
            )
        )


    # =========================================================
    # FECHAR ESPAÇO NA ORDENAÇÃO
    # =========================================================

    def close_space_after_position(
        self,
        deleted_position: int,
    ) -> None:

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


    # =========================================================
    # CRIAR
    # =========================================================

    def create(
        self,
        eco,
    ):

        self.db.add(
            eco
        )

        self.db.flush()

        return eco


    # =========================================================
    # EXCLUIR
    # =========================================================

    def delete(
        self,
        eco,
    ) -> None:

        self.db.delete(
            eco
        )