import sys
from pathlib import Path
from datetime import date, datetime

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.issue_test import IssueProcessor


def test_hold_suspension_end_to_end():

    processor = IssueProcessor()

    # Select a member
    member_id = next(iter(processor.members))

    # Select two copies
    selected_copies = list(processor.copies.values())[:2]

    assert len(selected_copies) == 2

    print("\nHOLD SUSPENSION END-TO-END TEST")
    print("================================")

    print("Member ID:", member_id)

    # Create two reserved holds
    for index, copy in enumerate(selected_copies):

        copy["status"] = "ON_HOLD_SHELF"
        copy["shelf_member_id"] = member_id

        expiry_date = (
            date(2026, 7, 5)
            if index == 0
            else date(2026, 7, 10)
        )

        processor.holds.append({
            "hold_id": f"HLD-TEST-{index + 1}",
            "title_id": copy["title_id"],
            "member_id": member_id,
            "placed_ts": datetime(2026, 7, 1, 10, index),
            "status": "ON_HOLD_SHELF",
            "shelf_copy_id": copy["copy_id"],
            "shelf_expiry_date": expiry_date
        })

    print("Initial reserved holds:", len(processor.holds))

    # First hold expires
    processor.apply_daily_events(date(2026, 7, 6))

    first_expiry_count = processor.hold_expiries[member_id][
        processor.semester_key(date(2026, 7, 6))
    ]

    print("\nAfter first expiry:")
    print("Expired holds:", first_expiry_count)

    # Second hold expires
    processor.apply_daily_events(date(2026, 7, 11))

    second_expiry_count = processor.hold_expiries[member_id][
        processor.semester_key(date(2026, 7, 11))
    ]

    print("\nAfter second expiry:")
    print("Expired holds:", second_expiry_count)
    print("Suspension until:", processor.hold_suspensions.get(member_id))

    # Check suspension
    suspended = processor.is_hold_suspended(
        member_id, date(2026, 7, 11)
    )

    print("Member suspended:", suspended)

    # Verify results
    assert first_expiry_count == 1
    assert second_expiry_count == 2
    assert suspended is True

    print("\nTEST PASSED!")
    print("Two missed pickups caused automatic suspension.")