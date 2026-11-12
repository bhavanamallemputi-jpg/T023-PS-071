import sys
from pathlib import Path
from datetime import datetime, date

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.issue_test import IssueProcessor


def test_member_cannot_hold_own_loan():

    processor = IssueProcessor()

    # Select a member with valid membership
    member = next(
        m for m in processor.members.values()
        if datetime.strptime(
            m["membership_expiry"], "%Y-%m-%d"
        ).date() >= date(2026, 7, 2)
    )

    member_id = member["member_id"]

    # Select a copy and its title
    copy = next(iter(processor.copies.values()))
    title_id = copy["title_id"]

    # Simulate the member borrowing this copy
    copy["status"] = "ISSUED"
    copy["member_id"] = member_id
    copy["issue_date"] = date(2026, 7, 1)
    copy["due_date"] = date(2026, 7, 15)

    print("\nOWN LOAN HOLD TEST")
    print("==================")

    print("Member ID:", member_id)
    print("Title ID:", title_id)
    print("Copy status:", copy["status"])

    # Try to place a hold on the same title
    result = processor.process_hold([
        "HOLD",
        member_id,
        title_id,
        "2026-07-02 10:00:00"
    ])

    print("Hold result:", result)

    assert result == "ON_LOAN_TO_MEMBER"

    print("\nTEST PASSED!")
    print("Member cannot hold a title already borrowed.")