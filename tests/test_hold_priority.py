import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.issue_test import IssueProcessor


def test_hold_priority():

    processor = IssueProcessor()

    faculty = next(
        (m for m in processor.members.values()
         if m["category"].strip().upper() == "FACULTY"),
        None
    )

    research = next(
        (m for m in processor.members.values()
         if m["category"].strip().upper() == "RESEARCH"),
        None
    )

    other = next(
        (m for m in processor.members.values()
         if m["category"].strip().upper() in ("UG", "PG", "EXTERNAL")),
        None
    )

    assert faculty is not None, "Faculty member not found"
    assert research is not None, "Research member not found"
    assert other is not None, "Other member not found"

    title_id = next(iter(processor.titles))

    processor.holds = [
        {
            "hold_id": "HLD-0001",
            "title_id": title_id,
            "member_id": other["member_id"],
            "placed_ts": datetime(2026, 7, 1, 10, 0),
            "status": "PENDING",
            "shelf_copy_id": None,
            "shelf_expiry_date": None
        },
        {
            "hold_id": "HLD-0002",
            "title_id": title_id,
            "member_id": research["member_id"],
            "placed_ts": datetime(2026, 7, 1, 11, 0),
            "status": "PENDING",
            "shelf_copy_id": None,
            "shelf_expiry_date": None
        },
        {
            "hold_id": "HLD-0003",
            "title_id": title_id,
            "member_id": faculty["member_id"],
            "placed_ts": datetime(2026, 7, 1, 12, 0),
            "status": "PENDING",
            "shelf_copy_id": None,
            "shelf_expiry_date": None
        }
    ]

    expected_order = [
        faculty["member_id"],
        research["member_id"],
        other["member_id"]
    ]

    actual_order = []

    for _ in range(3):

        hold = processor.get_next_hold(title_id)

        assert hold is not None

        actual_order.append(hold["member_id"])
        hold["status"] = "COLLECTED"

    assert actual_order == expected_order

    print("\nHOLD PRIORITY TEST PASSED!")
    print("Faculty: First priority")
    print("Research: Second priority")
    print("Other members: Third priority")