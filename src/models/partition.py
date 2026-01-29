from datetime import datetime, timedelta

from sqlalchemy import event
from sqlalchemy.engine import Engine

from models.models import Order


def create_partition_if_not_exists(engine, table_name, partition_key_value):
    """Создает новую партицию по месяцам если она не существует."""
    year = partition_key_value.year
    month = partition_key_value.month
    partition_name = f"{table_name}_{year}_{month:02d}"

    with engine.connect() as conn:
        exists = conn.execute(
            f"SELECT 1 FROM pg_tables WHERE tablename = {partition_name}"
        ).scalar()

    if not exists:
        start_date = datetime(year, month, 1)
        end_date = start_date + timedelta(days=32)
        end_date = end_date.replace(day=1)

        with engine.connect() as conn:
            conn.execute(
                f"""
                CREATE TABLE {partition_name} PARTITION OF {table_name}
                FOR VALUES FROM ('{start_date.isoformat()}')
                TO ('{end_date.isoformat()}')
                """
            )
            conn.execute(
                f"""
                CREATE INDEX {partition_name}_idx_order_customer
                ON {partition_name} (customer_id)
                """
            )
            conn.commit()


@event.listens_for(Engine, "before_execute")
def before_execute(conn, clauseelement, multiparams, params):
    if (
        hasattr(clauseelement, "insert")
        and clauseelement.insert.table.name == Order.__tablename__
    ):
        created_at = params.get("created_at") or datetime.now()
        create_partition_if_not_exists(conn.engine, Order.__tablename__, created_at)
    return clauseelement, multiparams, params
