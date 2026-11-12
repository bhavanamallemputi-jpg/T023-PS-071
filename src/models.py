from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Member:
    member_id: str
    member_name: str
    gender: str
    category: str
    department: str
    mobile: str
    membership_start: date
    membership_expiry: date
    opening_balance: float
    standing: str


@dataclass
class Title:
    title_id: str
    title: str
    author: str
    category: str
    department: str
    publication_year: int


@dataclass
class Copy:
    copy_id: str
    title_id: str
    price: float
    acquired_date: date
    shelf_location: str
    status: str = "AVAILABLE"
    member_id: Optional[str] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None


@dataclass
class Partner:
    partner_id: str
    partner_name: str
    city: str
    transit_days: int
    loan_period_days: int


@dataclass
class PartnerHolding:
    partner_id: str
    isbn: str
    title: str
    ill_charge: float
    replacement_price: float