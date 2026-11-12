import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.issue_test import IssueProcessor


def test_member_hold_limit():

    processor = IssueProcessor()

    member_id = next(iter(processor.members))
    title_id = next(iter(processor.titles))

    # Create three active holds
    for i in range(3):

        processor.holds.append({
            "hold_id": f"HLD-{i+1:04d}",
            "title_id": title_id,
            "member_id": member_id,
            "placed_ts": datetime(2026, 7, 1, 10, i),
            "status": "PENDING",
            "shelf_copy_id": None,
            "shelf_expiry_date": None
        })

    print("\nHOLD LIMIT TEST")
    print("================")

    existing_holds = len(
        processor.active_holds_for_member(member_id)
    )

    print("Existing active holds:", existing_holds)

    result = processor.process_hold([
        "HOLD",
        member_id,
        title_id,
        "2026-07-02 10:00:00"
    ])

    print("Fourth hold result:", result)

    assert existing_holds == 3
    assert result == "HOLD_LIMIT"

    print("\nTEST PASSED!")
    print("Fourth hold correctly rejected.")