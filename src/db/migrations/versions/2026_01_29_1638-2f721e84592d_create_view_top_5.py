"""create view top 5

Revision ID: 2f721e84592d
Revises: 6dc844573d3e
Create Date: 2026-01-29 16:38:50.085727

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2f721e84592d"
down_revision: Union[str, Sequence[str], None] = "6dc844573d3e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS top5_best_sellers_last_month_mat
        AS
        WITH sold AS (
            SELECT
                n.id AS nomenclature_id,
                n.name AS product_name,
                c_best.id AS category_id,
                c_best.path AS category_path,
                SUM(oi.amount) AS total_sold
            FROM orderitem oi
            JOIN "order" o ON o.id = oi.order_id AND o.created_at = oi.created_at
            JOIN nomenclature n ON n.id = oi.nomenclature_id
            LEFT JOIN LATERAL (
                SELECT pc.category_id
                FROM productcategory pc
                JOIN category c ON c.id = pc.category_id
                WHERE pc.nomenclature_id = n.id
                ORDER BY nlevel(c.path) ASC NULLS LAST
                LIMIT 1
            ) pc_choose ON true
            LEFT JOIN category c_best ON c_best.id = pc_choose.category_id
            WHERE o.created_at >= now() - INTERVAL '30 days'
            GROUP BY n.id, n.name, c_best.id, c_best.path
        )
        SELECT
            nomenclature_id,
            product_name,
            subpath(category_path, 0, 1)::text AS top_level_path,
            (SELECT name FROM category WHERE path = subpath(sold.category_path, 0, 1) LIMIT 1) AS top_level_category,
            total_sold
        FROM sold
        ORDER BY total_sold DESC
        LIMIT 5;
        """
    )

    # op.execute(
    #     """
    #     CREATE INDEX IF NOT EXISTS idx_mv_top5_total_sold
    #     ON top5_best_sellers_last_month_mat (total_sold DESC);
    #     """
    # )
    # op.execute(
    #     """
    #     DO $$
    #     BEGIN
    #         IF NOT EXISTS (
    #             SELECT 1 FROM pg_class c
    #             JOIN pg_index i ON i.indexrelid = c.oid
    #             WHERE c.relname = 'idx_mv_top5_unique_nomenclature_id'
    #         ) THEN
    #             BEGIN
    #                 CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_mv_top5_unique_nomenclature_id
    #                 ON top5_best_sellers_last_month_mat (nomenclature_id);
    #             EXCEPTION WHEN undefined_table THEN
    #                 RAISE NOTICE 'Unable to create unique index concurrently on materialized view (ignored).';
    #             END;
    #         END IF;
    #     END
    #     $$;
    #     """
    # )

    # op.execute(
    #     """
    #     CREATE OR REPLACE FUNCTION refresh_top5_best_sellers()
    #     RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
    #     BEGIN
    #         BEGIN
    #             EXECUTE 'REFRESH MATERIALIZED VIEW CONCURRENTLY top5_best_sellers_last_month_mat';
    #         EXCEPTION WHEN others THEN
    #             PERFORM 'REFRESH MATERIALIZED VIEW top5_best_sellers_last_month_mat';
    #         END;
    #     END;
    #     $$;
    #     """
    # )

    # 4) Попытка создать периодическое задание через pg_cron (если расширение установлено).
    #    Задание запускает функцию обновления каждые 30 минут.
    #    Если pg_cron не установлен, создавание job не выполнится (проверяем наличие pg_cron schema)
    # op.execute(
    #     """
    #     DO $$
    #     BEGIN
    #         IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron') THEN
    #             PERFORM cron.schedule(
    #                 'refresh_top5_best_sellers_job',
    #                 '*/30 * * * *',
    #                 $$SELECT refresh_top5_best_sellers()$$
    #             );
    #         ELSE
    #             RAISE NOTICE 'pg_cron not installed; skipping scheduling of refresh job.';
    #         END IF;
    #     EXCEPTION WHEN undefined_function THEN
    #         RAISE NOTICE 'pg_cron functions not available; skipping scheduling of refresh job.';
    #     END
    #     $$;
    #     """
    # )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron') THEN
                DELETE FROM cron.job WHERE command LIKE '%refresh_top5_best_sellers()%';
            END IF;
        EXCEPTION WHEN undefined_table THEN
            -- nothing
        END
        $$;
        """
    )

    op.execute("DROP FUNCTION IF EXISTS refresh_top5_best_sellers();")
    op.execute("DROP INDEX IF EXISTS idx_mv_top5_unique_nomenclature_id;")
    op.execute("DROP INDEX IF EXISTS idx_mv_top5_total_sold;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS top5_best_sellers_last_month_mat;")
