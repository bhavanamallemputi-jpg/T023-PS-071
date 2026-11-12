import sys
from pathlib import Path
from datetime import date, datetime

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.issue_test import IssueProcessor


def test_suspended_member_cannot_place_hold():

    processor = IssueProcessor()

    # Select two members with valid membership
    valid_members = [
        m for m in processor.members.values()
        if datetime.strptime(
            m["membership_expiry"], "%Y-%m-%d"
        ).date() >= date(2026, 7, 15)
    ]

    assert len(valid_members) >= 2

    suspended_member = valid_members[0]["member_id"]
    borrower = valid_members[1]["member_id"]

    # Select a title with copies
    title_id = next(iter(processor.titles))

    title_copies = [
        c for c in processor.copies.values()
        if c["title_id"] == title_id
    ]

    assert len(title_copies) > 0

    # Make all copies issued to another member
    for copy in title_copies:
        copy["status"] = "ISSUED"
        copy["member_id"] = borrower

    # Apply a 30-day hold suspension
    processor.hold_suspensions[suspended_member] = date(2026, 8, 10)

    print("\nSUSPENDED MEMBER HOLD TEST")
    print("=========================")

    print("Member ID:", suspended_member)
    print("Suspension until:", processor.hold_suspensions[suspended_member])
    print("Title ID:", title_id)

    # Try placing a hold during suspension
    result = processor.process_hold([
        "HOLD",
        suspended_member,
        title_id,
        "2026-07-15 10:00:00"
    ])

    print("\nHold placement result:", result)

    assert result == "HOLD_PRIVILEGE_SUSPENDED"

    print("\nTEST PASSED!")
    print("Suspended member cannot place a hold.")