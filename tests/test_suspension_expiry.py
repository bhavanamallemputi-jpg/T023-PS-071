import sys
from pathlib import Path
from datetime import date, datetime

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.issue_test import IssueProcessor


def test_suspension_expiry():

    processor = IssueProcessor()

    # Select two valid members
    valid_members = [
        m for m in processor.members.values()
        if datetime.strptime(
            m["membership_expiry"], "%Y-%m-%d"
        ).date() >= date(2026, 8, 11)
    ]

    assert len(valid_members) >= 2

    member_id = valid_members[0]["member_id"]
    borrower_id = valid_members[1]["member_id"]

    # Select a title
    title_id = next(iter(processor.titles))

    # Make all copies issued to another member
    title_copies = [
        c for c in processor.copies.values()
        if c["title_id"] == title_id
    ]

    assert len(title_copies) > 0

    for copy in title_copies:
        copy["status"] = "ISSUED"
        copy["member_id"] = borrower_id

    # Set suspension end date
    processor.hold_suspensions[member_id] = date(2026, 8, 10)

    # Check on the final suspension day
    before_expiry = processor.is_hold_suspended(
        member_id, date(2026, 8, 10)
    )

    # Check after the suspension period
    after_expiry = processor.is_hold_suspended(
        member_id, date(2026, 8, 11)
    )

    # Try placing a hold after suspension
    result = processor.process_hold([
        "HOLD",
        member_id,
        title_id,
        "2026-08-11 10:00:00"
    ])

    assert before_expiry is True
    assert after_expiry is False
    assert result == "SUCCESS"