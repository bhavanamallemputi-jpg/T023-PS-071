from datetime import datetime, timedelta

# Loan limits based on member category
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

SPECIAL_PERIODS = {
    "JOURNAL": 7,
    "DVD": 7
}


def is_closed_day(check_date, closed_days):
    return check_date in closed_days


def next_open_day(check_date, closed_days):
    while is_closed_day(check_date, closed_days):
        check_date += timedelta(days=1)

    return check_date


def calculate_due_date(issue_date, loan_period, closed_days):
    due_date = issue_date + timedelta(days=loan_period)
    return next_open_day(due_date, closed_days)


def calculate_fine(due_date, return_date, item_category, item_price, closed_days):
    fine = 0

    current_date = due_date + timedelta(days=1)

    while current_date <= return_date:

        if current_date not in closed_days:

            if item_category in ("JOURNAL", "DVD"):
                fine += 10

            else:
                overdue_days = 0

                check_date = due_date + timedelta(days=1)

                while check_date <= current_date:
                    if check_date not in closed_days:
                        overdue_days += 1

                    check_date += timedelta(days=1)

                if overdue_days > 1:
                    if overdue_days <= 8:
                        fine += 2
                    else:
                        fine += 5

        current_date += timedelta(days=1)

    return min(fine, 500, item_price)


def get_loan_period(member_category, item_category):

    if item_category in SPECIAL_PERIODS:
        return SPECIAL_PERIODS[item_category]

    if item_category in ("REFERENCE", "THESIS"):
        if member_category == "FACULTY":
            return 2
        return None

    return LOAN_PERIODS.get(member_category)


def get_loan_limit(member_category):
    return LOAN_LIMITS.get(member_category)


if __name__ == "__main__":

    closed_days = {
        datetime.strptime("2026-07-04", "%Y-%m-%d").date(),
        datetime.strptime("2026-07-05", "%Y-%m-%d").date()
    }

    issue_date = datetime.strptime(
        "2026-07-01", "%Y-%m-%d"
    ).date()

    loan_period = 14

    due_date = calculate_due_date(
        issue_date,
        loan_period,
        closed_days
    )

    print("LIBRARY CIRCULATION TEST")
    print("------------------------")
    print("Issue Date:", issue_date)
    print("Due Date:", due_date)

    return_date = datetime.strptime(
        "2026-07-20", "%Y-%m-%d"
    ).date()

    fine = calculate_fine(
        due_date,
        return_date,
        "BOOK",
        300,
        closed_days
    )

    print("Return Date:", return_date)
    print("Fine:", fine)