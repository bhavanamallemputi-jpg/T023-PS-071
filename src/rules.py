# Membership borrowing limits
LOAN_LIMITS = {
    "UG": 3,
    "PG": 5,
    "RESEARCH": 8,
    "FACULTY": 10,
    "EXTERNAL": 2
}

# Loan periods in days
LOAN_PERIODS = {
    "UG": 14,
    "PG": 21,
    "RESEARCH": 30,
    "FACULTY": 90,
    "EXTERNAL": 7
}

# Special item loan periods
SPECIAL_LOAN_PERIODS = {
    "JOURNAL": 7,
    "DVD": 7
}

# Fine rates
NORMAL_FINE_FIRST_7_DAYS = 2
NORMAL_FINE_AFTER_7_DAYS = 5
SPECIAL_FINE_RATE = 10

# Other library rules
MAX_FINE = 500
FINE_BLOCK_LIMIT = 200
MAX_RENEWALS = 2
MAX_HOLDS_PER_MEMBER = 3
MAX_OVERDUE_DAYS_FOR_BLOCK = 30

REFERENCE_LOAN_PERIOD = 2
REFERENCE_LOAN_LIMIT = 2

MAX_HOLD_SUSPENSION_DAYS = 30
HOLD_PICKUP_DAYS = 3

ILL_FINE_PER_DAY = 20
ILL_MINIMUM_LOAN_DAYS = 7


def get_loan_limit(member_category):
    return LOAN_LIMITS.get(member_category.upper(), 0)


def get_loan_period(member_category, item_category):
    item_category = item_category.upper()
    member_category = member_category.upper()

    if item_category in SPECIAL_LOAN_PERIODS:
        return SPECIAL_LOAN_PERIODS[item_category]

    if item_category in ("REFERENCE", "THESIS"):
        if member_category == "FACULTY":
            return REFERENCE_LOAN_PERIOD
        return 0

    return LOAN_PERIODS.get(member_category, 0)


def calculate_fine(overdue_days, item_category, item_price):
    item_category = item_category.upper()

    if overdue_days <= 0:
        return 0.0

    if item_category in ("JOURNAL", "DVD"):
        fine = overdue_days * SPECIAL_FINE_RATE
    else:
        chargeable_days = max(0, overdue_days - 1)

        first_7_days = min(chargeable_days, 7)
        remaining_days = max(0, chargeable_days - 7)

        fine = (
            first_7_days * NORMAL_FINE_FIRST_7_DAYS
            + remaining_days * NORMAL_FINE_AFTER_7_DAYS
        )

    return round(min(fine, MAX_FINE, item_price), 2)


def can_renew(renewal_count):
    return renewal_count < MAX_RENEWALS


def can_place_hold(copy_statuses):
    return len(copy_statuses) > 0 and all(
        status == "ISSUED" for status in copy_statuses
    )