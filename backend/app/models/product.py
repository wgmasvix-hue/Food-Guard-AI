from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import FormulationStatus


class Product(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "products"

    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    allergens: Mapped[str | None] = mapped_column(Text)  # comma-separated allergen list
    shelf_life_days: Mapped[int | None] = mapped_column()
    storage_conditions: Mapped[str | None] = mapped_column(Text)
    intended_use: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    company = relationship("Company")
    ingredients: Mapped[list["Ingredient"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    batches: Mapped[list["Batch"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    formulations: Mapped[list["ProductFormulation"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="ProductFormulation.version.desc()"
    )


class Ingredient(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ingredients"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    supplier_id: Mapped[str | None] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(20))
    is_allergen: Mapped[bool] = mapped_column(Boolean, default=False)

    product: Mapped[Product] = relationship(back_populates="ingredients")
    supplier = relationship("Supplier")


class Batch(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "batches"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    facility_id: Mapped[str | None] = mapped_column(ForeignKey("facilities.id", ondelete="SET NULL"))
    batch_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    production_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    quantity: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(50), default="in_production")  # in_production/released/on_hold/recalled

    product: Mapped[Product] = relationship(back_populates="batches")


class ProductFormulation(Base, UUIDMixin, TimestampMixin):
    """A versioned recipe/formulation for a product. Each save-as-new-version
    creates a new row (full history kept) rather than mutating in place —
    only one version per product is normally "active" at a time."""

    __tablename__ = "product_formulations"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[FormulationStatus] = mapped_column(String(20), default=FormulationStatus.DRAFT)
    batch_size: Mapped[float | None] = mapped_column(Float)  # reference batch size the item quantities are for
    batch_size_unit: Mapped[str | None] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    approved_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    product: Mapped[Product] = relationship(back_populates="formulations")
    created_by = relationship("User", foreign_keys=[created_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    items: Mapped[list["FormulationItem"]] = relationship(
        back_populates="formulation", cascade="all, delete-orphan", order_by="FormulationItem.created_at"
    )

    @property
    def total_percentage(self) -> float:
        return sum(item.percentage or 0 for item in self.items)

    @property
    def total_cost(self) -> float:
        return sum((item.unit_cost or 0) * (item.quantity or 0) for item in self.items)

    @property
    def allergens(self) -> list[str]:
        return [item.name for item in self.items if item.is_allergen]


class FormulationItem(Base, UUIDMixin, TimestampMixin):
    """One ingredient line within a ProductFormulation version."""

    __tablename__ = "formulation_items"

    formulation_id: Mapped[str] = mapped_column(ForeignKey("product_formulations.id", ondelete="CASCADE"), index=True)
    supplier_id: Mapped[str | None] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    percentage: Mapped[float | None] = mapped_column(Float)  # % of total formulation composition
    quantity: Mapped[float | None] = mapped_column(Float)  # absolute quantity for the formulation's batch_size
    unit: Mapped[str | None] = mapped_column(String(20))
    unit_cost: Mapped[float | None] = mapped_column(Float)  # cost per unit of quantity
    is_allergen: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)

    formulation: Mapped[ProductFormulation] = relationship(back_populates="items")
    supplier = relationship("Supplier")
