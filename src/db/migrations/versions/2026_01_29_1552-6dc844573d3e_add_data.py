"""add data

Revision ID: 6dc844573d3e
Revises: e70de171b6db
Create Date: 2026-01-29 15:52:35.000511

"""

from datetime import datetime, timedelta
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6dc844573d3e"
down_revision: Union[str, Sequence[str], None] = "e70de171b6db"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Настраиваемые параметры
NUM_PRODUCTS = 100_000
NUM_CATEGORIES = 5_000
NUM_CUSTOMERS = 50_000
NUM_ORDERS = 200_000
AVG_ITEMS_PER_ORDER = 3

# Параметры дерева категорий
TOP_LEVEL_COUNT = 20  # число корневых категорий
MAX_DEPTH = 10  # максимальная глубина (включая корень)
BRANCH_FACTOR = 3  # максимальное число детей у узла


def _month_range(start_dt: datetime, end_dt: datetime):
    cur = datetime(start_dt.year, start_dt.month, 1)
    end = datetime(end_dt.year, end_dt.month, 1)
    while cur <= end:
        yield cur.year, cur.month
        if cur.month == 12:
            cur = datetime(cur.year + 1, 1, 1)
        else:
            cur = datetime(cur.year, cur.month + 1, 1)


def upgrade() -> None:
    """Заполнить базу тестовыми данными, создать партиции для 'order', и сгенерировать дерево категорий BFS."""

    # === 1) Категории: BFS-генерация в PL/pgSQL с использованием временной таблицы tmp_new_cats ===
    op.execute(
        f"""
        DO $$
        DECLARE
            target integer := {NUM_CATEGORIES};
            top_count integer := {TOP_LEVEL_COUNT};
            bf integer := {BRANCH_FACTOR};
            max_depth integer := {MAX_DEPTH};
            created integer := 0;
            next_id integer := 1;
            cur_level integer := 1;
        BEGIN
            -- временная таблица для очереди: cid, path_text, depth
            CREATE TEMP TABLE IF NOT EXISTS tmp_cat_queue (cid integer, path_text text, depth integer) ON COMMIT DROP;
            -- временная таблица для новых узлов на итерации
            CREATE TEMP TABLE IF NOT EXISTS tmp_new_cats (id integer, path_text text) ON COMMIT DROP;

            -- вставляем корни
            INSERT INTO category (id, name, path)
            SELECT i, ('Category ' || i::text), i::text::ltree
            FROM generate_series(1, LEAST(top_count, target)) AS s(i)
            ON CONFLICT (id) DO NOTHING;

            created := LEAST(top_count, target);
            next_id := created + 1;

            -- заполним очередь текущими корнями
            DELETE FROM tmp_cat_queue;
            INSERT INTO tmp_cat_queue (cid, path_text, depth)
            SELECT id, id::text, 1 FROM category
            WHERE id BETWEEN 1 AND created;

            -- цикл по уровням (BFS)
            WHILE created < target AND cur_level < max_depth LOOP
                -- очищаем таблицу новых кандидатов
                DELETE FROM tmp_new_cats;

                WITH parents AS (
                    SELECT cid, path_text
                    FROM tmp_cat_queue
                    WHERE depth = cur_level
                    ORDER BY cid
                ),
                gen AS (
                    SELECT p.cid AS parent_id, p.path_text AS parent_path, gs AS seq_in_parent
                    FROM parents p
                    CROSS JOIN generate_series(1, bf) gs
                ),
                candidates AS (
                    SELECT gen.parent_id,
                           gen.parent_path || '.' || gen.seq_in_parent::text AS path_text,
                           ROW_NUMBER() OVER (ORDER BY gen.parent_id, gen.seq_in_parent) AS rn
                    FROM gen
                )
                INSERT INTO tmp_new_cats (id, path_text)
                SELECT next_id + (c.rn - 1) AS id, c.path_text
                FROM candidates c
                WHERE (next_id + (c.rn - 1)) <= target;

                -- вставляем новые категории
                INSERT INTO category (id, name, path)
                SELECT id, ('Category ' || id::text), path_text::ltree
                FROM tmp_new_cats
                ON CONFLICT (id) DO NOTHING;

                -- добавляем вставленные узлы в очередь для следующего уровня
                INSERT INTO tmp_cat_queue (cid, path_text, depth)
                SELECT id, path_text, cur_level + 1 FROM tmp_new_cats
                ON CONFLICT DO NOTHING;

                -- обновляем счётчики
                SELECT COALESCE(MAX(id), next_id - 1) INTO STRICT created FROM category;
                next_id := created + 1;
                cur_level := cur_level + 1;
            END LOOP;
        END
        $$;
        """
    )

    # === 2) Товары ===
    op.execute(
        f"""
        INSERT INTO nomenclature (id, name, amount, price, created_at)
        SELECT gs,
               ('Product ' || gs::text),
               ( (random() * 1000)::int ),
               (round((random()*1000 + 1)::numeric, 2)),
               NOW() - ( (random() * 365)::int || ' days')::interval
        FROM generate_series(1, {NUM_PRODUCTS}) AS gs
        ON CONFLICT (id) DO NOTHING;
        """
    )

    # === 3) Связи товар->категория ===
    op.execute(
        f"""
        WITH prod AS (SELECT id AS pid FROM nomenclature ORDER BY id LIMIT {NUM_PRODUCTS}),
        cat_ids AS (SELECT id FROM category ORDER BY id),
        assign AS (
            SELECT p.pid AS nomenclature_id,
                   ( (floor(random() * (SELECT count(*) FROM cat_ids)) + 1)::int )::int as category_id
            FROM prod p
            CROSS JOIN generate_series(1,3) g
        )
        INSERT INTO productcategory (nomenclature_id, category_id)
        SELECT DISTINCT nomenclature_id, category_id
        FROM assign
        WHERE category_id IS NOT NULL
        ON CONFLICT DO NOTHING;
        """
    )

    # === 4) Клиенты ===
    op.execute(
        f"""
        INSERT INTO customer (id, name, address, created_at)
        SELECT gs,
               ('Customer ' || gs::text),
               ('Address ' || gs::text),
               NOW() - ( (random() * 365)::int || ' days')::interval
        FROM generate_series(1, {NUM_CUSTOMERS}) AS gs
        ON CONFLICT (id) DO NOTHING;
        """
    )

    # === 5) Заказы: создаём партиции покрывающие диапазон дат, затем вставляем заказы ===

    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=180)

    for year, month in _month_range(start_dt, end_dt):
        part_name = f"order_{year}_{month:02d}"
        from_dt = datetime(year, month, 1)
        if month == 12:
            to_dt = datetime(year + 1, 1, 1)
        else:
            to_dt = datetime(year, month + 1, 1)

        op.execute(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_class WHERE relname = '{part_name}'
                ) THEN
                    EXECUTE $sql$
                        CREATE TABLE {part_name} PARTITION OF "order"
                        FOR VALUES FROM ('{from_dt.isoformat()}') TO ('{to_dt.isoformat()}')
                    $sql$;
                END IF;
            END
            $$;
            """
        )

        op.execute(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_class WHERE relname = '{part_name}_idx_order_customer'
                ) THEN
                    EXECUTE $sql$
                        CREATE INDEX {part_name}_idx_order_customer ON {part_name} (customer_id);
                    $sql$;
                END IF;
            END
            $$;
            """
        )

    # Вставляем заказы (Postgres распределит по партициям)
    op.execute(
        f"""
        WITH gen_orders AS (
            SELECT gs AS order_id,
                   (NOW() - (floor(random()*180)::int || ' days')::interval
                    - (floor(random()*86400)::int || ' seconds')::interval) AS created_at,
                   ((floor(random() * {NUM_CUSTOMERS}) + 1)::int) AS customer_id
            FROM generate_series(1, {NUM_ORDERS}) AS gs
        )
        INSERT INTO "order" (id, created_at, customer_id)
        SELECT order_id, created_at, customer_id FROM gen_orders
        ON CONFLICT DO NOTHING;
        """
    )

    # Материализация заказов во временную таблицу
    op.execute(
        f"""
        CREATE TEMP TABLE tmp_orders ON COMMIT DROP AS
        SELECT id AS order_id, created_at
        FROM "order"
        ORDER BY id
        LIMIT {NUM_ORDERS};
        """
    )

    # Генерация позиций заказов во временную таблицу
    op.execute(
        f"""
        CREATE TEMP TABLE tmp_orderitems ON COMMIT DROP AS
        SELECT
            o.order_id,
            o.created_at,
            p.pid AS nomenclature_id,
            ( (floor(random()*10) + 1)::int ) AS amount,
            (round((p.price)::numeric, 2)) AS price
        FROM (
            SELECT order_id, created_at,
                   (floor(random() * ({AVG_ITEMS_PER_ORDER}*2)::numeric) + 1)::int AS item_count
            FROM tmp_orders
        ) o
        JOIN LATERAL (
            SELECT gs AS seq,
                   ( (floor(random() * {NUM_PRODUCTS}) + 1)::int ) AS pid,
                   (round((random()*1000 + 1)::numeric, 2)) AS price
            FROM generate_series(1, o.item_count) gs
        ) p ON true;
        """
    )

    # Вставка позиций заказов
    op.execute(
        """
        INSERT INTO orderitem (order_id, created_at, nomenclature_id, amount, price)
        SELECT order_id, created_at, nomenclature_id, amount, price
        FROM tmp_orderitems
        ON CONFLICT DO NOTHING;
        """
    )

    # Индексы на родительской таблице (создаём если отсутствуют)
    op.execute(
        """CREATE INDEX IF NOT EXISTS idx_order_created_at ON "order" (created_at);"""
    )
    op.execute(
        """CREATE INDEX IF NOT EXISTS idx_order_customer ON "order" (customer_id);"""
    )
    op.execute(
        """CREATE INDEX IF NOT EXISTS idx_orderitem_order ON orderitem (order_id, created_at);"""
    )
    op.execute(
        """CREATE INDEX IF NOT EXISTS idx_orderitem_nomenclature ON orderitem (nomenclature_id);"""
    )


def downgrade() -> None:
    """Удаление данных, добавленных этой миграцией. Партиции не удаляются автоматически."""
    op.execute(
        f"""
        DELETE FROM orderitem
        WHERE order_id BETWEEN 1 AND {NUM_ORDERS}
          AND nomenclature_id BETWEEN 1 AND {NUM_PRODUCTS};
        """
    )
    op.execute(
        f"""
        DELETE FROM "order"
        WHERE id BETWEEN 1 AND {NUM_ORDERS};
        """
    )
    op.execute(
        f"""
        DELETE FROM productcategory
        WHERE nomenclature_id BETWEEN 1 AND {NUM_PRODUCTS};
        """
    )
    op.execute(
        f"""
        DELETE FROM nomenclature
        WHERE id BETWEEN 1 AND {NUM_PRODUCTS}
          AND name LIKE 'Product %';
        """
    )
    op.execute(
        f"""
        DELETE FROM customer
        WHERE id BETWEEN 1 AND {NUM_CUSTOMERS}
          AND name LIKE 'Customer %';
        """
    )
    op.execute(
        f"""
        DELETE FROM category
        WHERE id BETWEEN 1 AND {NUM_CATEGORIES}
          AND name LIKE 'Category %';
        """
    )
