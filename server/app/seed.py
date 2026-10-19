import os
from datetime import date, timedelta

from sqlalchemy import select

from app.config.database import SessionLocal
from app.models.entities import (
    User,
    Eco,
    ObuAuMapping,
    OwnerGroupMapping,
)
from app.utils.security import hash_password


# =========================================================
# Credenciais do ambiente DEMO
# Devem ser configuradas por variáveis de ambiente no Render
# =========================================================
ADMIN_EMAIL = os.getenv("DEMO_ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("DEMO_ADMIN_PASSWORD")


def main():
    # ---------------------------------------------------------
    # Validação das variáveis de ambiente
    # ---------------------------------------------------------
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        raise RuntimeError(
            "DEMO_ADMIN_EMAIL e DEMO_ADMIN_PASSWORD "
            "precisam estar configurados."
        )

    db = SessionLocal()

    try:
        # ---------------------------------------------------------
        # Usuário administrador de demonstração
        # ---------------------------------------------------------
        admin = db.scalar(
            select(User).where(
                User.email == ADMIN_EMAIL
            )
        )

        if not admin:
            db.add(
                User(
                    email=ADMIN_EMAIL,
                    full_name="Administrador Demo",
                    hashed_password=hash_password(
                        ADMIN_PASSWORD
                    ),
                    role="admin",
                )
            )

        # ---------------------------------------------------------
        # Mapeamento OBU -> AU
        # Dados totalmente fictícios para demonstração
        # ---------------------------------------------------------
        obu_au_mappings = {
            "D01": "AU1",
            "D02": "AU1",
            "D03": "AU2",
            "D04": "AU2",
            "D05": "AU3",
            "D06": "AU3",
        }

        for obu, au in obu_au_mappings.items():
            existing_mapping = db.scalar(
                select(ObuAuMapping).where(
                    ObuAuMapping.obu == obu
                )
            )

            if not existing_mapping:
                db.add(
                    ObuAuMapping(
                        obu=obu,
                        au=au,
                    )
                )

        # ---------------------------------------------------------
        # Mapeamento Owner -> Group
        # Dados totalmente fictícios
        # ---------------------------------------------------------
        owner_group_mappings = {
            "analista.demo01": "BOM",
            "analista.demo02": "BOM",
            "analista.demo03": "HW",
            "analista.demo04": "MEC",
            "analista.demo05": "DEV",
            "analista.demo06": "MEC",
        }

        for owner, group_name in (
            owner_group_mappings.items()
        ):
            existing_mapping = db.scalar(
                select(OwnerGroupMapping).where(
                    OwnerGroupMapping.owner
                    == owner
                )
            )

            if not existing_mapping:
                db.add(
                    OwnerGroupMapping(
                        owner=owner,
                        group_name=group_name,
                    )
                )

        # ---------------------------------------------------------
        # Dados sintéticos de ECO
        # ---------------------------------------------------------
        existing_eco = db.scalar(
            select(Eco).limit(1)
        )

        if existing_eco is None:
            samples = []

            months = [
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
            ]

            obus = list(
                obu_au_mappings.keys()
            )

            owner_names = list(
                owner_group_mappings.keys()
            )

            statuses = (
                ["RELEASED"] * 8
                + ["CANCELLED"] * 3
                + ["WORKING"] * 3
                + ["PROCESSING"] * 2
            )

            eco_types = [
                "REGULAR",
                "DESENHO",
                "SOFTWARE",
                "TEMP",
                "DESENHO - IMPRESSOS/BOX",
            ]

            base_date = date(
                2026,
                1,
                5,
            )

            for i in range(1, 31):
                creation_date = (
                    base_date
                    + timedelta(
                        days=i * 8
                    )
                )

                gap_days = (
                    i % 20
                ) + 1

                approval_finish_date = (
                    creation_date
                    + timedelta(
                        days=gap_days
                    )
                )

                obu = obus[
                    i % len(obus)
                ]

                owner = owner_names[
                    i % len(
                        owner_names
                    )
                ]

                group_name = (
                    owner_group_mappings[
                        owner
                    ]
                )

                au = (
                    obu_au_mappings[
                        obu
                    ]
                )

                eco = Eco(
                    item=i,
                    position=i,

                    month=months[
                        (i - 1)
                        % len(months)
                    ],

                    product=(
                        "PROD-DEMO"
                    ),

                    obu=obu,
                    au=au,

                    group_name=(
                        group_name
                    ),

                    owner=owner,

                    item_type=(
                        "MEC"
                        if i % 3
                        else "ELET"
                    ),

                    eco_type=(
                        eco_types[
                            i
                            % len(
                                eco_types
                            )
                        ]
                    ),

                    status=(
                        statuses[
                            i
                            % len(
                                statuses
                            )
                        ]
                    ),

                    eco=(
                        f"DEMO{i:05d}"
                    ),

                    change_bom=(
                        "YES"
                        if i % 2
                        else "NO"
                    ),

                    hq_eco_release_date=(
                        creation_date
                        - timedelta(
                            days=5
                        )
                    ),

                    az_eco_register_date=(
                        creation_date
                        - timedelta(
                            days=3
                        )
                    ),

                    az_eco_creation_date=(
                        creation_date
                    ),

                    second_aprov_rd_finish_1=(
                        approval_finish_date
                    ),

                    comments=(
                        "Dado totalmente fictício "
                        "utilizado somente no "
                        "ambiente de demonstração."
                    ),
                )

                samples.append(
                    eco
                )

            db.add_all(
                samples
            )

        # ---------------------------------------------------------
        # Salva as alterações
        # ---------------------------------------------------------
        db.commit()

        print(
            "Seed de demonstração "
            "concluído com sucesso. "
            f"Usuário: {ADMIN_EMAIL}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()