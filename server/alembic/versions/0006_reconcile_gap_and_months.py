"""Reconcile GAP report fields and normalize stored month abbreviations."""

from alembic import op
import sqlalchemy as sa


revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    columns = {
        column["name"]
        for column in sa.inspect(bind).get_columns("ecos")
    }

    # Compatibilidade com bancos que vieram do develop,
    # onde a antiga revision 0004 era a normalização dos meses.
    if "effective_date" not in columns:
        op.add_column(
            "ecos",
            sa.Column(
                "effective_date",
                sa.Date(),
                nullable=True,
            ),
        )

    if "gap_14d_note" not in columns:
        op.add_column(
            "ecos",
            sa.Column(
                "gap_14d_note",
                sa.Text(),
                nullable=True,
            ),
        )

    # Normaliza abreviações antigas em inglês para português.
    op.execute(
        """
        UPDATE ecos
        SET month = CASE UPPER(TRIM(month))
            WHEN 'JAN' THEN 'JAN'
            WHEN 'FEB' THEN 'FEV'
            WHEN 'MAR' THEN 'MAR'
            WHEN 'APR' THEN 'ABR'
            WHEN 'MAY' THEN 'MAI'
            WHEN 'JUN' THEN 'JUN'
            WHEN 'JUL' THEN 'JUL'
            WHEN 'AUG' THEN 'AGO'
            WHEN 'SEP' THEN 'SET'
            WHEN 'OCT' THEN 'OUT'
            WHEN 'NOV' THEN 'NOV'
            WHEN 'DEC' THEN 'DEZ'
            ELSE month
        END
        WHERE month IS NOT NULL
          AND UPPER(TRIM(month)) IN (
              'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
              'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'
          )
        """
    )


def downgrade():
    op.execute(
        """
        UPDATE ecos
        SET month = CASE UPPER(TRIM(month))
            WHEN 'JAN' THEN 'JAN'
            WHEN 'FEV' THEN 'FEB'
            WHEN 'MAR' THEN 'MAR'
            WHEN 'ABR' THEN 'APR'
            WHEN 'MAI' THEN 'MAY'
            WHEN 'JUN' THEN 'JUN'
            WHEN 'JUL' THEN 'JUL'
            WHEN 'AGO' THEN 'AUG'
            WHEN 'SET' THEN 'SEP'
            WHEN 'OUT' THEN 'OCT'
            WHEN 'NOV' THEN 'NOV'
            WHEN 'DEZ' THEN 'DEC'
            ELSE month
        END
        WHERE month IS NOT NULL
          AND UPPER(TRIM(month)) IN (
              'JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN',
              'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ'
          )
        """
    )