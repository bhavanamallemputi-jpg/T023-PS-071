import sys
from pathlib import Path
from datetime import datetime, date

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.issue_test import IssueProcessor


def test_successful_hold():

    processor = IssueProcessor()

    # Select two different members with valid membership
    valid_members = [
        m for m in processor.members.values()
        if datetime.strptime(
            m["membership_expiry"], "%Y-%m-%d"
        ).date() >= date(2026, 7, 2)
    ]

    assert len(valid_members) >= 2

    member_id = valid_members[0]["member_id"]

    borrower_id = next(
        m["member_id"] for m in valid_members
        if m["member_id"] != member_id
    )

    # Select a title
    title_id = next(iter(processor.titles))

    title_copies = [
        c for c in processor.copies.values()
        if c["title_id"] == title_id
    ]

    assert len(title_copies) > 0

    # Make every copy issued to another member
    for copy in title_copies:
        copy["status"] = "ISSUED"
        copy["member_id"] = borrower_id

    print("\nSUCCESSFUL HOLD TEST")
    print("====================")

    print("Title ID:", title_id)
    print("Member placing hold:", member_id)
    print("Number of copies:", len(title_copies))

    # Place the hold
    result = processor.process_hold([
        "HOLD",
        member_id,
        title_id,
        "2026-07-02 10:00:00"
    ])

    print("Hold result:", result)

    assert result == "SUCCESS"
    assert len(processor.holds) == 1
    assert processor.holds[0]["status"] == "PENDING"

    print("\nTEST PASSED!")
    print("Hold successfully placed.")