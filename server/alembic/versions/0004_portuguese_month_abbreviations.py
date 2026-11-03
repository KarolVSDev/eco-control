"""Normalize stored month abbreviations to Portuguese."""

from alembic import op


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
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