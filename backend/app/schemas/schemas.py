"""Pydantic v2 schemas — every API input validated here."""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

CATEGORIES = [
    "seeds", "fertilizer", "pesticide", "labor", "fuel", "irrigation",
    "equipment", "transport", "electricity", "rent", "insurance", "other",
]

ExpenseCategory = Literal[
    "seeds", "fertilizer", "pesticide", "labor", "fuel", "irrigation",
    "equipment", "transport", "electricity", "rent", "insurance", "other",
]


# ---------- auth ----------
class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    mobile: str = Field(min_length=10, max_length=15)
    password: str = Field(min_length=6, max_length=72)
    language: str = "en"

    @field_validator("mobile")
    @classmethod
    def digits_only(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("mobile must contain digits only")
        return v


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    mobile: str
    language: str
    is_demo: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LanguageUpdate(BaseModel):
    language: Literal["en", "hi", "mr"]


# ---------- farms ----------
class FarmCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    area_acres: float = Field(gt=0, le=10000)
    latitude: float | None = None
    longitude: float | None = None
    village: str | None = Field(default=None, max_length=120)


class FarmOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    area_acres: float
    latitude: float | None
    longitude: float | None
    village: str | None


# ---------- crops ----------
class CropCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    area_acres: float = Field(gt=0, le=10000)
    sowing_date: date | None = None
    expected_yield_quintal: float | None = Field(default=None, gt=0)
    expected_price_per_quintal: float | None = Field(default=None, gt=0)


class CropOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    farm_id: int
    name: str
    area_acres: float
    sowing_date: date | None
    expected_yield_quintal: float | None
    expected_price_per_quintal: float | None
    status: str


# ---------- expenses ----------
class ExpenseCreate(BaseModel):
    category: ExpenseCategory
    amount: float = Field(gt=0, le=10_000_000)
    crop_id: int | None = None
    spent_on: date | None = None
    note: str | None = Field(default=None, max_length=500)
    source: Literal["manual", "voice", "ocr"] = "manual"


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    crop_id: int | None
    category: str
    amount: float
    spent_on: date
    note: str | None
    source: str


# ---------- production ----------
class ProductionCreate(BaseModel):
    harvest_date: date
    actual_yield_quintal: float = Field(gt=0)
    note: str | None = Field(default=None, max_length=500)


class ProductionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    crop_id: int
    harvest_date: date
    actual_yield_quintal: float
    note: str | None


# ---------- sales ----------
class SaleCreate(BaseModel):
    sale_date: date
    quantity_quintal: float = Field(gt=0)
    price_per_quintal: float = Field(gt=0)
    transport_cost: float = Field(default=0, ge=0)
    other_charges: float = Field(default=0, ge=0)
    buyer: str | None = Field(default=None, max_length=120)


class SaleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    crop_id: int
    sale_date: date
    quantity_quintal: float
    price_per_quintal: float
    transport_cost: float
    other_charges: float
    buyer: str | None


# ---------- analytics ----------
class DashboardOut(BaseModel):
    total_investment: float
    total_revenue: float
    net_profit: float
    roi_percent: float
    active_crops: int
    total_farms: int
    upcoming_harvests: int
    pending_sales: int
    this_month_expenses: float
    largest_category: str | None
    largest_category_amount: float


class CropProfitOut(BaseModel):
    crop_id: int
    crop_name: str
    area_acres: float
    total_cost: float
    revenue: float
    profit: float
    roi_percent: float
    cost_per_acre: float
    profit_per_acre: float
    break_even_price_per_quintal: float | None
    produced_quintal: float
    sold_quintal: float
    expected_yield_quintal: float | None
    production_variance_percent: float | None


class CropComparisonRow(BaseModel):
    crop_name: str
    profit: float
    roi_percent: float
    profit_per_acre: float
    is_best: bool


class SimulatorRequest(BaseModel):
    price_per_quintal: float = Field(gt=0)
    production_quintal: float | None = Field(default=None, gt=0)
    cost_multiplier: float = Field(default=1.0, gt=0)


class SimulatorOut(BaseModel):
    revenue: float
    total_cost: float
    profit: float
    break_even_price_per_quintal: float
    sold_out: bool


class Insight(BaseModel):
    title: str
    detail: str
    severity: Literal["info", "good", "warning"]


# ---------- ai ----------
class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    answer: str
    provider: str


# ---------- weather ----------
class ForecastDay(BaseModel):
    date: date
    temp_min_c: float
    temp_max_c: float
    precipitation_mm: float
    precipitation_probability_percent: int
    weather_code: int


class WeatherOut(BaseModel):
    latitude: float
    longitude: float
    days: list[ForecastDay]
    advisory: list[str]
    cached: bool


# ---------- market ----------
class MarketPriceRow(BaseModel):
    commodity: str
    market: str
    min_price: float | None
    max_price: float | None
    modal_price: float | None
    price_date: date | None
    source: str


# ---------- notifications ----------
class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: str
    title: str
    body: str | None
    read_at: datetime | None
    created_at: datetime


# ---------- location ----------
class GeocodeRequest(BaseModel):
    query: str = Field(min_length=3, max_length=200)


class GeocodeResult(BaseModel):
    display_name: str
    latitude: float
    longitude: float


# ---------- ocr ----------
class OCRResult(BaseModel):
    amount: float | None
    category: ExpenseCategory | None
    vendor: str | None
    date: date | None
    raw_text: str
    demo: bool


# ---------- integrations ----------
class IntegrationStatus(BaseModel):
    name: str
    live: bool
    detail: str
