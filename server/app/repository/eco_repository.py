from sqlalchemy import (
    func,
    or_,
    select,
    update,
)
from sqlalchemy.orm import Session

from app.models.entities import (
    Eco,
    EcoHistory,
)


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
    # PRÓXIMO ITEM
    # =========================================================

    def next_item(
        self,
    ):

        current_max = (
            self.db.scalar(
                select(
                    func.max(
                        Eco.item
                    )
                )
            )
            or 0
        )


        history_max = (
            self.db.scalar(
                select(
                    func.max(
                        EcoHistory.item
                    )
                )
            )
            or 0
        )


        return (
            max(
                current_max,
                history_max,
            )
            + 1
        )


    # =========================================================
    # PRÓXIMA POSITION
    # =========================================================

    def next_position(
        self,
    ):

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
    ):

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
    ):

        self.db.delete(
            eco
        )