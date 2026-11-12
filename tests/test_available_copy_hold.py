import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.issue_test import IssueProcessor


def test_hold_rejected_when_copy_available():

    processor = IssueProcessor()

    # Select a title and one of its copies
    copy = next(iter(processor.copies.values()))

    title_id = copy["title_id"]
    member_id = next(iter(processor.members))

    # Make sure the copy is available
    copy["status"] = "AVAILABLE"

    print("\nAVAILABLE COPY HOLD TEST")
    print("=========================")

    print("Title ID:", title_id)
    print("Copy status:", copy["status"])

    # Attempt to place a hold
    result = processor.process_hold([
        "HOLD",
        member_id,
        title_id,
        "2026-07-02 10:00:00"
    ])

    print("Hold result:", result)

    assert result == "COPIES_AVAILABLE"

    print("\nTEST PASSED!")
    print("Hold correctly rejected because a copy is available.")