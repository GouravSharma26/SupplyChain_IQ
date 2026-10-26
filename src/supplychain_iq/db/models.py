"""SQLAlchemy 2.0 declarative relational models for SupplyChain IQ."""

from datetime import date
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base class for all relational models."""
    pass


class Supplier(Base):
    """Supplier entity capturing lead time baseline and reliability rating."""
    __tablename__ = "suppliers"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="Unknown")
    lead_time_days: Mapped[float] = mapped_column(Float, nullable=False, default=7.0)
    reliability_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.95)

    products: Mapped[List["Product"]] = relationship(
        "Product", back_populates="supplier", cascade="all, delete-orphan"
    )
    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship(
        "PurchaseOrder", back_populates="supplier", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("lead_time_days >= 0", name="chk_supplier_lead_time_nonneg"),
        CheckConstraint("reliability_score >= 0.0 AND reliability_score <= 1.0", name="chk_reliability_score_range"),
    )

    def __repr__(self) -> str:
        return f"<Supplier(id='{self.id}', name='{self.name}', lead_time={self.lead_time_days}d)>"


class Product(Base):
    """Product/SKU entity capturing costs, categories, and operational parameters."""
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="General")
    unit_cost: Mapped[float] = mapped_column(Float, nullable=False)
    selling_price: Mapped[float] = mapped_column(Float, nullable=False)
    min_order_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    supplier_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True
    )

    supplier: Mapped[Optional["Supplier"]] = relationship("Supplier", back_populates="products")
    daily_demands: Mapped[List["DailyDemand"]] = relationship(
        "DailyDemand", back_populates="product", cascade="all, delete-orphan"
    )
    inventory_snapshots: Mapped[List["InventorySnapshot"]] = relationship(
        "InventorySnapshot", back_populates="product", cascade="all, delete-orphan"
    )
    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship(
        "PurchaseOrder", back_populates="product", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("unit_cost >= 0", name="chk_product_unit_cost_nonneg"),
        CheckConstraint("selling_price >= 0", name="chk_product_selling_price_nonneg"),
        CheckConstraint("min_order_qty >= 0", name="chk_product_min_order_qty_nonneg"),
    )

    def __repr__(self) -> str:
        return f"<Product(id='{self.id}', name='{self.name}', cost=${self.unit_cost:.2f})>"


class DailyDemand(Base):
    """Daily demand/sales observation grain (Date x Product)."""
    __tablename__ = "daily_demand"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    product_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    units_sold: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    channel: Mapped[str] = mapped_column(String(50), nullable=False, default="Omnichannel")
    promotion_applied: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    product: Mapped["Product"] = relationship("Product", back_populates="daily_demands")

    __table_args__ = (
        CheckConstraint("units_sold >= 0", name="chk_daily_demand_units_sold_nonneg"),
        Index("idx_daily_demand_date_product", "date", "product_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<DailyDemand(date={self.date}, product='{self.product_id}', sold={self.units_sold})>"


class InventorySnapshot(Base):
    """Periodic inventory snapshot recording stock on hand and safety stock targets."""
    __tablename__ = "inventory_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    product_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    inventory_on_hand: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    safety_stock_target: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    stockout_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    product: Mapped["Product"] = relationship("Product", back_populates="inventory_snapshots")

    __table_args__ = (
        CheckConstraint("inventory_on_hand >= 0", name="chk_snapshot_stock_nonneg"),
        Index("idx_inv_snapshot_date_product", "date", "product_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<InventorySnapshot(date={self.date}, product='{self.product_id}', stock={self.inventory_on_hand})>"


class PurchaseOrder(Base):
    """Purchase and delivery order tracking supplier fulfillment performance and delays."""
    __tablename__ = "purchase_orders"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    product_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    supplier_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False
    )
    order_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Delivered")
    is_late: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    delay_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    product: Mapped["Product"] = relationship("Product", back_populates="purchase_orders")
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="purchase_orders")

    __table_args__ = (
        CheckConstraint("order_quantity > 0", name="chk_po_qty_positive"),
        CheckConstraint("unit_cost >= 0", name="chk_po_cost_nonneg"),
        CheckConstraint("delay_days >= 0", name="chk_po_delay_nonneg"),
        Index("idx_po_supplier_date", "supplier_id", "order_date"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder(id='{self.id}', supplier='{self.supplier_id}', qty={self.order_quantity}, late={self.is_late})>"
