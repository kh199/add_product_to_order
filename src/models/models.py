from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import backref, mapped_column, relationship

from src.db.db import Base, IntegerIdMixin


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


class Category(Base, IntegerIdMixin):
    name = mapped_column(Text, comment="Наименование", nullable=False)
    parent_id = mapped_column(
        Integer, ForeignKey("category.id", ondelete="SET NULL"), default=None
    )
    parent = relationship(
        "Category",
        remote_side=[id],
        backref=backref("children", cascade="all, delete-orphan"),
    )
    product_categories = relationship(
        "ProductCategory", back_populates="category", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("name", "parent_id", name="uq_category_name_parent"),
        Index("idx_category_parent", "parent_id"),
    )


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
    nomenclature = relationship("Nomenclature", back_populates="order_items")
    order = relationship("Order", back_populates="order_items")

    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_order_item_amount_positive"),
        CheckConstraint("price >= 0", name="chk_order_item_price_non_negative"),
        Index("idx_oi_order", "order_id"),
        Index("idx_oi_nomenclature", "nomenclature_id"),
    )
