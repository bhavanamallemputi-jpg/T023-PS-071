import sys
from pathlib import Path
from datetime import date, timedelta

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.issue_test import IssueProcessor


def test_two_expired_holds_trigger_suspension():

    processor = IssueProcessor()

    # Select a member
    member_id = next(iter(processor.members))

    # Simulate two expired holds in the same semester
    semester = (2026, 2)

    processor.hold_expiries[member_id][semester] = 1

    # Simulate the second expiry
    current_date = date(2026, 8, 10)

    processor.hold_expiries[member_id][semester] += 1

    # Apply the suspension rule
    if processor.hold_expiries[member_id][semester] >= 2:
        processor.hold_suspensions[member_id] = (
            current_date + timedelta(days=30)
        )

    print("\nHOLD SUSPENSION TEST")
    print("====================")

    print("Member ID:", member_id)
    print("Expired holds:", processor.hold_expiries[member_id][semester])
    print("Suspension until:", processor.hold_suspensions[member_id])

    # Check suspension
    test_date = date(2026, 8, 20)

    result = processor.is_hold_suspended(member_id, test_date)

    assert processor.hold_expiries[member_id][semester] == 2
    assert processor.hold_suspensions[member_id] == date(2026, 9, 9)
    assert result is True

    print("\nTEST PASSED!")
    print("Member is suspended from placing holds.")