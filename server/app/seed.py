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


ADMIN_EMAIL = "admin@eco.com"
ADMIN_PASSWORD = "admin123"


def main():
    db = SessionLocal()

    try:
        # ---------------------------------------------------------
        # Usuário administrador local
        # ---------------------------------------------------------
        admin = db.scalar(
            select(User).where(User.email == ADMIN_EMAIL)
        )

        if not admin:
            db.add(
                User(
                    email=ADMIN_EMAIL,
                    full_name="Administrador Local",
                    hashed_password=hash_password(ADMIN_PASSWORD),
                    role="admin",
                )
            )

        # ---------------------------------------------------------
        # Mapeamento OBU -> AU
        # ---------------------------------------------------------
        obu_au_mappings = {
            "NW1": "GLZ",
            "NWD": "GLZ",
            "NWE": "GLZ",
            "NWZ": "GLZ",
            "NWH": "GMZ",
            "NWW": "GMZ",
            "NWU": "PNZ",
            "NWX": "PNZ",
            "NWV": "PGZ",
            "NWK": "LMZ",
            "NYE": "GMZ",
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
        # ---------------------------------------------------------
        owner_group_mappings = {
            "kamila.pimentel": "BOM",
            "giseli.santos": "BOM",
            "maria.ribeiro": "HW",
            "leandro.moraes": "MEC",
            "wallacea.roberto": "DEV",
            "adriano.junior": "MEC",
        }

        for owner, group_name in owner_group_mappings.items():
            existing_mapping = db.scalar(
                select(OwnerGroupMapping).where(
                    OwnerGroupMapping.owner == owner
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
                "SEP",
                "NOV",
            ]

            obus = [
                "NWH",
                "NW1",
                "NWE",
                "NWZ",
                "NWU",
                "NWV",
            ]

            owner_names = list(
                owner_group_mappings.keys()
            )

            statuses = (
                ["RELEASED"] * 8
                + ["CANCELLED"] * 3
                + ["WORKING", "PROCESSING"]
            )

            eco_types = [
                "REGULAR",
                "DESENHO",
                "SOFTWARE",
                "TEMP",
                "DESENHO - IMPRESSOS/BOX",
            ]

            base_date = date(2026, 1, 1)

            for i in range(1, 31):
                creation_date = (
                    base_date
                    + timedelta(days=i * 2)
                )

                gap_days = (i % 20) + 1

                approval_finish_date = (
                    creation_date
                    + timedelta(days=gap_days)
                )

                obu = obus[
                    i % len(obus)
                ]

                owner = owner_names[
                    i % len(owner_names)
                ]

                group_name = (
                    owner_group_mappings[owner]
                )

                au = obu_au_mappings.get(obu)

                eco = Eco(
                    item=i,
                    position=i,

                    month=months[
                        i % len(months)
                    ],

                    product="AAA",

                    obu=obu,
                    au=au,

                    group_name=group_name,
                    owner=owner,

                    item_type=(
                        "MEC"
                        if i % 3
                        else "ELET"
                    ),

                    eco_type=eco_types[
                        i % len(eco_types)
                    ],

                    status=statuses[
                        i % len(statuses)
                    ],

                    eco=f"DEMO{i:05d}",

                    change_bom=(
                        "YES"
                        if i % 2
                        else "NO"
                    ),

                    hq_eco_release_date=(
                        creation_date
                        - timedelta(days=5)
                    ),

                    az_eco_register_date=(
                        creation_date
                        - timedelta(days=3)
                    ),

                    az_eco_creation_date=(
                        creation_date
                    ),

                    second_aprov_rd_finish_1=(
                        approval_finish_date
                    ),

                    comments=(
                        "Dado sintético para "
                        "desenvolvimento local"
                    ),
                )

                samples.append(eco)

            db.add_all(samples)

        # ---------------------------------------------------------
        # Salva tudo
        # ---------------------------------------------------------
        db.commit()

        print(
            "Seed concluído. "
            f"Login: {ADMIN_EMAIL} / {ADMIN_PASSWORD}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()