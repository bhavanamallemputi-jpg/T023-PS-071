import sys
from pathlib import Path
from datetime import date, datetime

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.issue_test import IssueProcessor


def test_expired_hold_collection():

    processor = IssueProcessor()

    # Select a member and title
    member_id = next(iter(processor.members))
    title_id = next(iter(processor.titles))

    # Select a copy
    copy = next(
        c for c in processor.copies.values()
        if c["title_id"] == title_id
    )

    copy_id = copy["copy_id"]

    # Put the copy on the hold shelf
    copy["status"] = "ON_HOLD_SHELF"
    copy["shelf_member_id"] = member_id

    # Create an expired hold
    processor.holds.append({
        "hold_id": "HLD-TEST",
        "title_id": title_id,
        "member_id": member_id,
        "placed_ts": datetime(2026, 7, 1, 10, 0),
        "status": "ON_HOLD_SHELF",
        "shelf_copy_id": copy_id,
        "shelf_expiry_date": date(2026, 7, 5)
    })

    print("\nEXPIRED HOLD COLLECTION TEST")
    print("============================")

    print("Member ID:", member_id)
    print("Copy ID:", copy_id)
    print("Hold expiry date: 2026-07-05")

    # Process events after expiry
    processor.apply_daily_events(date(2026, 7, 6))

    hold = processor.holds[0]

    print("\nAfter expiry processing:")
    print("Hold status:", hold["status"])
    print("Copy status:", copy["status"])
    print("Assigned member:", copy.get("shelf_member_id"))

    # Verify expiry
    assert hold["status"] == "EXPIRED"
    assert copy["status"] == "AVAILABLE"
    assert copy.get("shelf_member_id") is None

    print("\nTEST PASSED!")
    print("Expired hold was cancelled.")
    print("Copy was released as available.")