"""Tests for SQLAlchemy relational models, constraints, and ETL loading."""

from datetime import date, timedelta
import pandas as pd
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from supplychain_iq.db.database import init_db
from supplychain_iq.db.etl import (
    load_from_curated_dataframe,
    query_curated_dataframe,
    query_supplier_fulfillment_metrics,
)
from supplychain_iq.db.models import (
    Base,
    DailyDemand,
    InventorySnapshot,
    Product,
    PurchaseOrder,
    Supplier,
)


@pytest.fixture
def in_memory_engine():
    """Create an isolated in-memory SQLite database engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    init_db(engine)
    return engine


@pytest.fixture
def db_session(in_memory_engine):
    """Provide a transactional database session."""
    session_factory = sessionmaker(bind=in_memory_engine, expire_on_commit=False)
    session = session_factory()
    yield session
    session.rollback()
    session.close()


def test_init_db_creates_all_tables(in_memory_engine):
    """Verify that all core entity tables exist in the relational metadata."""
    expected_tables = {
        "suppliers",
        "products",
        "daily_demand",
        "inventory_snapshots",
        "purchase_orders",
    }
    assert expected_tables.issubset(set(Base.metadata.tables.keys()))


def test_entity_relationships_and_foreign_keys(db_session):
    """Verify relational model navigation across suppliers, products, and demands."""
    sup = Supplier(
        id="SUP-TEST-1",
        name="Test Supplier Ltd",
        country="Canada",
        lead_time_days=5.0,
        reliability_score=0.95,
    )
    prod = Product(
        id="SKU-TEST-1",
        name="Industrial Sensor",
        category="Electronics",
        unit_cost=50.0,
        selling_price=85.0,
        min_order_qty=10,
        supplier=sup,
    )
    demand = DailyDemand(
        date=date(2026, 10, 1),
        product=prod,
        units_sold=25.0,
        channel="Wholesale",
        promotion_applied=False,
    )
    snap = InventorySnapshot(
        date=date(2026, 10, 1),
        product=prod,
        inventory_on_hand=150.0,
        safety_stock_target=35.0,
        stockout_flag=False,
    )
    po = PurchaseOrder(
        id="PO-TEST-1",
        order_date=date(2026, 9, 20),
        expected_delivery_date=date(2026, 9, 25),
        actual_delivery_date=date(2026, 9, 27),
        product=prod,
        supplier=sup,
        order_quantity=100,
        unit_cost=50.0,
        status="Delivered",
        is_late=True,
        delay_days=2,
    )

    db_session.add_all([sup, prod, demand, snap, po])
    db_session.commit()

    # Test inverse navigation
    queried_sup = db_session.get(Supplier, "SUP-TEST-1")
    assert queried_sup is not None
    assert len(queried_sup.products) == 1
    assert queried_sup.products[0].id == "SKU-TEST-1"
    assert len(queried_sup.purchase_orders) == 1
    assert queried_sup.purchase_orders[0].is_late is True

    queried_prod = db_session.get(Product, "SKU-TEST-1")
    assert queried_prod.daily_demands[0].units_sold == 25.0
    assert queried_prod.inventory_snapshots[0].inventory_on_hand == 150.0


def test_schema_constraints_enforce_valid_data(db_session):
    """Verify check constraints prevent negative quantities or costs."""
    sup = Supplier(
        id="SUP-FAIL",
        name="Fail Supplier",
        lead_time_days=-3.0,  # Negative lead time violated
        reliability_score=0.8,
    )
    db_session.add(sup)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    prod = Product(
        id="SKU-FAIL",
        name="Fail Product",
        unit_cost=-10.0,  # Negative cost violated
        selling_price=20.0,
        min_order_qty=5,
    )
    db_session.add(prod)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_etl_loading_and_idempotency(db_session):
    """Verify raw DataFrame ingestion, normalization, and idempotent repeated loading."""
    dates = pd.date_range("2026-05-01", periods=10, freq="D")
    sample_df = pd.DataFrame({
        "date": dates,
        "product_id": ["SKU-001"] * 10,
        "product_name": ["Widget Pro"] * 10,
        "category": ["Components"] * 10,
        "units_sold": [10.0, 12.0, 8.0, 15.0, 20.0, 14.0, 18.0, 22.0, 9.0, 11.0],
        "inventory_on_hand": [100.0, 90.0, 82.0, 67.0, 47.0, 33.0, 15.0, 93.0, 84.0, 73.0],
        "unit_cost": [15.50] * 10,
        "lead_time_days": [7.0] * 10,
    })

    # Initial Ingestion
    res1 = load_from_curated_dataframe(db_session, sample_df)
    db_session.commit()
    assert res1.status == "SUCCESS"
    assert res1.products_loaded == 1
    assert res1.daily_demands_loaded == 10
    assert res1.snapshots_loaded == 10
    assert res1.purchase_orders_loaded > 0

    # Repeat loading same dataframe (Idempotency check)
    res2 = load_from_curated_dataframe(db_session, sample_df)
    db_session.commit()
    assert res2.status == "SUCCESS"
    assert res2.products_loaded == 0  # No new products added
    assert res2.daily_demands_loaded == 0  # Updated in place, no duplicate rows

    # Verify count of daily demand rows in DB remains 10
    demand_count = db_session.execute(select(DailyDemand)).scalars().all()
    assert len(demand_count) == 10


def test_query_curated_dataframe(db_session):
    """Verify curated query matches the application contract schema."""
    dates = pd.date_range("2026-06-01", periods=5, freq="D")
    sample_df = pd.DataFrame({
        "date": dates,
        "product_id": ["SKU-A"] * 5,
        "product_name": ["Alpha Sensor"] * 5,
        "category": ["Sensors"] * 5,
        "units_sold": [10.0, 15.0, 12.0, 18.0, 20.0],
        "inventory_on_hand": [50.0, 35.0, 23.0, 5.0, 85.0],
        "unit_cost": [45.0] * 5,
        "lead_time_days": [6.0] * 5,
    })
    load_from_curated_dataframe(db_session, sample_df)
    db_session.commit()

    curated_df = query_curated_dataframe(db_session)
    assert len(curated_df) == 5
    assert "date" in curated_df.columns
    assert "units_sold" in curated_df.columns
    assert "inventory_on_hand" in curated_df.columns
    assert "unit_cost" in curated_df.columns
    assert "supplier_name" in curated_df.columns


def test_query_supplier_fulfillment_metrics(db_session):
    """Verify empirical on-time delivery rates and delay day summaries."""
    sup = Supplier(id="SUP-METRIC", name="Metric Logistics", lead_time_days=7.0, reliability_score=0.90)
    prod = Product(id="SKU-METRIC", name="Metric SKU", unit_cost=10.0, selling_price=15.0, min_order_qty=10, supplier=sup)
    db_session.add_all([sup, prod])
    db_session.flush()

    # 3 on-time orders, 1 late order (delay=4)
    pos = [
        PurchaseOrder(
            id="PO-M1", order_date=date(2026, 1, 1), expected_delivery_date=date(2026, 1, 8),
            actual_delivery_date=date(2026, 1, 8), product=prod, supplier=sup, order_quantity=100,
            unit_cost=10.0, status="Delivered", is_late=False, delay_days=0
        ),
        PurchaseOrder(
            id="PO-M2", order_date=date(2026, 1, 15), expected_delivery_date=date(2026, 1, 22),
            actual_delivery_date=date(2026, 1, 22), product=prod, supplier=sup, order_quantity=100,
            unit_cost=10.0, status="Delivered", is_late=False, delay_days=0
        ),
        PurchaseOrder(
            id="PO-M3", order_date=date(2026, 2, 1), expected_delivery_date=date(2026, 2, 8),
            actual_delivery_date=date(2026, 2, 8), product=prod, supplier=sup, order_quantity=100,
            unit_cost=10.0, status="Delivered", is_late=False, delay_days=0
        ),
        PurchaseOrder(
            id="PO-M4", order_date=date(2026, 2, 15), expected_delivery_date=date(2026, 2, 22),
            actual_delivery_date=date(2026, 2, 26), product=prod, supplier=sup, order_quantity=100,
            unit_cost=10.0, status="Delivered", is_late=True, delay_days=4
        ),
    ]
    db_session.add_all(pos)
    db_session.commit()

    metrics = query_supplier_fulfillment_metrics(db_session)
    assert len(metrics) == 1
    row = metrics.iloc[0]
    assert row["supplier_id"] == "SUP-METRIC"
    assert row["total_orders"] == 4
    assert row["late_orders"] == 1
    assert row["on_time_rate"] == 0.75
    assert row["avg_delay_days"] == 1.0


def test_etl_rejects_malformed_dataframe(db_session):
    """Verify that malformed data is rejected before writing to database."""
    malformed_df = pd.DataFrame({
        "bad_column_1": [1, 2],
        "bad_column_2": ["a", "b"],
    })
    result = load_from_curated_dataframe(db_session, malformed_df)
    assert result.status == "REJECTED"
    assert result.rejected_rows == 2
    assert len(result.rejection_reasons) > 0

    # Ensure no rows were added to the database
    prod_count = db_session.execute(select(Product)).scalars().all()
    assert len(prod_count) == 0
