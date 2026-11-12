import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.issue_test import IssueProcessor


def test_recalled_book_double_fine():

    processor = IssueProcessor()

    due_date = date(2026, 7, 1)
    return_date = date(2026, 7, 20)

    # Calculate normal late fine
    normal_fine = processor.calculate_fine(
        due_date,
        return_date,
        "BOOK",
        10000,
        recalled=False
    )

    # Calculate recalled book late fine
    recalled_fine = processor.calculate_fine(
        due_date,
        return_date,
        "BOOK",
        10000,
        recalled=True
    )

    expected_fine = min(normal_fine * 2, 500, 10000)

    print("\nRECALLED BOOK FINE TEST")
    print("=======================")
    print("Normal fine: Rs.", normal_fine)
    print("Recalled fine: Rs.", recalled_fine)
    print("Expected recalled fine: Rs.", expected_fine)

    assert normal_fine > 0
    assert recalled_fine == expected_fine

    print("\nTEST PASSED!")
    print("Recalled books receive double late fines.")