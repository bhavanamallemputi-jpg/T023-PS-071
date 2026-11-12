import sys
from pathlib import Path
from datetime import date, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.issue_test import IssueProcessor


def test_book_recall():

    processor = IssueProcessor()

    title_id = "TTL-0001"

    title_copies = [
        copy for copy in processor.copies.values()
        if copy["title_id"] == title_id
    ]

    assert len(title_copies) >= 2

    recall_date = date(2026, 7, 20)

    for index, copy in enumerate(title_copies):

        copy["status"] = "ISSUED"
        copy["member_id"] = f"MEM-{index + 1:04d}"
        copy["issue_date"] = date(2026, 7, 1) + timedelta(days=index)
        copy["due_date"] = date(2026, 7, 30)
        copy["recalled"] = False

    recalled_id = processor.recall_longest_held_copy(
        title_id,
        recall_date
    )

    print("\nRecalled copy:", recalled_id)

    assert recalled_id == title_copies[0]["copy_id"]
    assert title_copies[0]["recalled"] is True

    print("TEST PASSED!")