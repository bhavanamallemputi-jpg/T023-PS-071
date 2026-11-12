import sys
from pathlib import Path
from datetime import date, datetime

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.issue_test import IssueProcessor


def test_hold_collection():

    processor = IssueProcessor()

    # Select two valid members
    valid_members = [
        m for m in processor.members.values()
        if datetime.strptime(
            m["membership_expiry"], "%Y-%m-%d"
        ).date() >= date(2026, 7, 2)
    ]

    assert len(valid_members) >= 2

    assigned_member = valid_members[0]["member_id"]
    other_member = valid_members[1]["member_id"]

    # Select a title and one of its copies
    title_id = next(iter(processor.titles))

    copy = next(
        c for c in processor.copies.values()
        if c["title_id"] == title_id
    )

    copy_id = copy["copy_id"]

    # Reserve the copy for the assigned member
    copy["status"] = "ON_HOLD_SHELF"
    copy["shelf_member_id"] = assigned_member

    processor.holds.append({
        "hold_id": "HLD-TEST",
        "title_id": title_id,
        "member_id": assigned_member,
        "placed_ts": datetime(2026, 7, 1, 10, 0),
        "status": "ON_HOLD_SHELF",
        "shelf_copy_id": copy_id,
        "shelf_expiry_date": date(2026, 7, 5)
    })

    print("\nHOLD COLLECTION TEST")
    print("====================")

    print("Copy ID:", copy_id)
    print("Assigned member:", assigned_member)
    print("Other member:", other_member)

    # Test 1: Wrong member tries to collect
    wrong_result = processor.issue_book(
        other_member,
        copy_id,
        "2026-07-02 10:00:00"
    )

    print("\nOther member collection result:", wrong_result)

    # Test 2: Assigned member tries to collect
    correct_result = processor.issue_book(
        assigned_member,
        copy_id,
        "2026-07-02 10:05:00"
    )

    print("Assigned member collection result:", correct_result)

    # Verify results
    assert wrong_result == "HOLD_EXISTS"
    assert correct_result == "SUCCESS"
    assert copy["status"] == "ISSUED"

    print("\nTEST PASSED!")
    print("Only the assigned member collected the reserved copy.")