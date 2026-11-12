import csv
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "output"


def read_csv(filename):
    file_path = OUTPUT_DIR / filename

    assert file_path.exists(), f"{filename} was not generated"

    with open(file_path, "r", newline="", encoding="utf-8") as file:
        return list(csv.reader(file))


def test_all_reports_exist():
    reports = [
        "issues.csv",
        "holds.csv",
        "member_ledger.csv",
        "circulation_log.csv",
        "member_status.csv",
    ]

    for report in reports:
        assert (OUTPUT_DIR / report).exists()


def test_issue_report_contains_records():
    rows = read_csv("issues.csv")
    assert len(rows) > 1


def test_lost_books_are_recorded():
    rows = read_csv("issues.csv")

    lost_records = [
        row for row in rows
        if "LOST" in row
    ]

    assert len(lost_records) > 0


def test_lost_book_returns_are_recorded():
    rows = read_csv("issues.csv")

    returned_lost = [
        row for row in rows
        if "RETURNED_AFTER_LOST" in row
    ]

    assert len(returned_lost) > 0


def test_lost_book_charges_are_recorded():
    rows = read_csv("member_ledger.csv")

    charge_types = [
        "LOST_REPLACEMENT",
        "LOST_PROCESSING",
        "LOST_FINE",
    ]

    for charge in charge_types:
        assert any(charge in row for row in rows)


def test_lost_book_refunds_are_recorded():
    rows = read_csv("circulation_log.csv")

    assert any(
        "LOST_ITEM_RETURNED_REPLACEMENT_REFUNDED" in row
        for row in rows
    )