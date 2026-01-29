from alembic_utils.pg_view import PGView

report_view = PGView(
    schema="public",
    signature="activity_view",
    definition="""
    SELECT n.name AS nomenclature_name,
        COALESCE(
            (SELECT c_parent.name FROM productcategory pc
            JOIN category c ON pc.category_id = c.id
            LEFT JOIN category c_parent ON c.parent_id = c_parent.id
            WHERE pc.nomenclature_id = n.id
            ORDER BY c_parent.id NULLS LAST
            LIMIT 1),
            'Без категории')
        AS top_level_category_name,
        SUM(oi.quantity) AS total_sold
    FROM nomenclature n
    JOIN order_item oi ON oi.nomenclature_id = n.id
    JOIN order o ON oi.order_id = o.id
    WHERE o.order_date >= (CURRENT_DATE - INTERVAL '1 month')
    GROUP BY n.id, n.name
    ORDER BY total_sold DESC
    LIMIT 5;
    """,
)
