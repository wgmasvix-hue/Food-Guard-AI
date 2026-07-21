from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


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
