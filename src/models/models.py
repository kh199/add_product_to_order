from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Sequence,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship, remote
from sqlalchemy_utils import Ltree, LtreeType

from src.db.db import Base, IntegerIdMixin, engine

id_seq = Sequence("nodes_id_seq")


class Nomenclature(Base, IntegerIdMixin):
    name = mapped_column(Text, comment="Наименование", nullable=False)
    amount = mapped_column(Integer, comment="Количество", default=0, nullable=False)
    price = mapped_column(Numeric, comment="Цена", nullable=False)
    categories = relationship(
        "ProductCategory", back_populates="nomenclature", cascade="all, delete-orphan"
    )
    order_items = relationship("OrderItem", back_populates="nomenclature")

    __table_args__ = (
        CheckConstraint("amount >= 0", name="chk_nomenclature_amount_non_negative"),
        Index("idx_nomenclature_name", "name"),
        Index("idx_nomenclature_price", "price"),
    )


class Category(Base):
    id = mapped_column(Integer, id_seq, primary_key=True)
    name = mapped_column(Text, comment="Наименование", nullable=False)
    path = mapped_column(LtreeType, nullable=False)
    parent = relationship(
        "Category",
        primaryjoin=remote(path) == foreign(func.subpath(path, 0, -1)),
        backref="children",
        viewonly=True,
    )
    product_categories = relationship(
        "ProductCategory", back_populates="category", cascade="all, delete-orphan"
    )

    def __init__(self, name, parent=None):
        _id = engine.execute(id_seq)
        self.id = _id
        self.name = name
        ltree_id = Ltree(str(_id))
        self.path = ltree_id if parent is None else parent.path + ltree_id

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Category({})".format(self.name)

    __table_args__ = (Index("idx_categories_path", path, postgresql_using="gist"),)


class ProductCategory(Base):
    nomenclature_id = mapped_column(
        Integer, ForeignKey("nomenclature.id", ondelete="CASCADE"), primary_key=True
    )
    category_id = mapped_column(
        Integer, ForeignKey("category.id", ondelete="CASCADE"), primary_key=True
    )
    nomenclature = relationship("Nomenclature", back_populates="categories")
    category = relationship("Category", back_populates="product_categories")
    __table_args__ = (
        UniqueConstraint(
            "nomenclature_id", "category_id", name="uq_nomenclature_category"
        ),
        Index("idx_pc_category", "category_id"),
        Index("idx_pc_nomenclature", "nomenclature_id"),
    )


class Customer(Base, IntegerIdMixin):
    name = mapped_column(Text, comment="Имя", nullable=False)
    address = mapped_column(Text, comment="Адрес", nullable=False)
    orders = relationship("Order", back_populates="customer")

    __table_args__ = (Index("idx_customer_name", "name"),)


class Order(Base, IntegerIdMixin):
    customer_id = mapped_column(Integer, ForeignKey("customer.id", ondelete="SET NULL"))
    customer = relationship("Customer", back_populates="orders")
    order_items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_order_customer", "customer_id"),
        Index("idx_order_date", "created_at"),
        {"postgresql_partition_by": "RANGE (created_at)"},
    )


class OrderItem(Base):
    order_id = mapped_column(
        Integer, ForeignKey("order.id", ondelete="CASCADE"), primary_key=True
    )
    nomenclature_id = mapped_column(
        Integer, ForeignKey("nomenclature.id", ondelete="CASCADE"), primary_key=True
    )
    amount = mapped_column(Integer, comment="Количество", nullable=False)
    price = mapped_column(Numeric, comment="Цена", nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата создания записи",
    )
    nomenclature = relationship("Nomenclature", back_populates="order_items")
    order = relationship("Order", back_populates="order_items")

    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_order_item_amount_positive"),
        CheckConstraint("price >= 0", name="chk_order_item_price_non_negative"),
        Index("idx_oi_order_created_at", "order_id", "created_at"),
        Index("idx_oi_nomenclature", "nomenclature_id"),
    )
