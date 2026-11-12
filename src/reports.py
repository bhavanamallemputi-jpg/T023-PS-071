import csv
from pathlib import Path


class ReportWriter:

    REPORT_SCHEMAS = {
        "circulation_log.csv": [
            "line_no",
            "command",
            "member_id",
            "copy_or_ref",
            "event_ts",
            "result",
            "reason",
            "due_date",
            "charge"
        ],

        "issues.csv": [
            "issue_id",
            "member_id",
            "copy_or_ill_id",
            "issue_date",
            "original_due_date",
            "current_due_date",
            "renewals",
            "recalled",
            "return_date",
            "status",
            "fine"
        ],

        "holds.csv": [
            "hold_id",
            "title_id",
            "member_id",
            "placed_ts",
            "status",
            "shelf_copy_id",
            "shelf_expiry_date"
        ],

        "member_ledger.csv": [
            "member_id",
            "entry_ts",
            "entry_type",
            "reference",
            "amount",
            "balance_after"
        ],

        "member_status.csv": [
            "member_id",
            "as_of_date",
            "items_on_loan",
            "outstanding",
            "max_overdue_days",
            "block_status",
            "block_reasons"
        ]
    }

    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_report(self, filename, rows):

        if filename not in self.REPORT_SCHEMAS:
            raise ValueError(f"Unknown report: {filename}")

        columns = self.REPORT_SCHEMAS[filename]

        file_path = self.output_dir / filename

        with open(
            file_path,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=columns,
                extrasaction="ignore"
            )

            writer.writeheader()
            writer.writerows(rows)

        print(f"Generated: {filename}")

    def write_all(self, reports):

        for filename, rows in reports.items():
            self.write_report(filename, rows)