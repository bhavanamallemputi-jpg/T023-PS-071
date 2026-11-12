import sys
from pathlib import Path
from datetime import datetime, date

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.issue_test import IssueProcessor


def test_hold_expiry_and_reassignment():

    processor = IssueProcessor()

    title_id = next(iter(processor.titles))

    members = list(processor.members.values())

    member1 = members[0]["member_id"]
    member2 = members[1]["member_id"]

    copy = next(
        c for c in processor.copies.values()
        if c["title_id"] == title_id
    )

    processor.holds = [
        {
            "hold_id": "HLD-0001",
            "title_id": title_id,
            "member_id": member1,
            "placed_ts": datetime(2026, 7, 1, 10, 0),
            "status": "ON_HOLD_SHELF",
            "shelf_copy_id": copy["copy_id"],
            "shelf_expiry_date": date(2026, 7, 4)
        },
        {
            "hold_id": "HLD-0002",
            "title_id": title_id,
            "member_id": member2,
            "placed_ts": datetime(2026, 7, 1, 11, 0),
            "status": "PENDING",
            "shelf_copy_id": None,
            "shelf_expiry_date": None
        }
    ]

    copy["status"] = "ON_HOLD_SHELF"
    copy["shelf_member_id"] = member1

    print("\nHOLD EXPIRY TEST")
    print("================")

    processor.apply_daily_events(date(2026, 7, 5))

    first_hold = processor.holds[0]
    second_hold = processor.holds[1]

    print("First hold status:", first_hold["status"])
    print("Second hold status:", second_hold["status"])
    print("Copy status:", copy["status"])
    print("New assigned member:", copy.get("shelf_member_id"))

    assert first_hold["status"] == "EXPIRED"
    assert second_hold["status"] == "ON_HOLD_SHELF"
    assert copy["shelf_member_id"] == member2

    print("\nTEST PASSED!")
    print("Expired hold was reassigned successfully.")