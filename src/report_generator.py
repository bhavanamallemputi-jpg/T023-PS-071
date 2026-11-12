import csv
from pathlib import Path
from datetime import date, datetime

from src.engine import LibraryEngine


class ReportGenerator:

    def __init__(self, engine):
        self.engine = engine

        self.output_dir = (
            Path(__file__).resolve().parent.parent / "output"
        )

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.member_status_rows = []

    @staticmethod
    def format_value(value):
        if isinstance(value, (date, datetime)):
            return value.isoformat()

        if value is None:
            return ""

        return value

    def write_csv(self, filename, columns, rows):
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

            for row in rows:
                writer.writerow({
                    key: self.format_value(value)
                    for key, value in row.items()
                })

        print(f"Generated: {filename}")

    # --------------------------------
    # ISSUES REPORT
    # --------------------------------

    def generate_issues_report(self):
        columns = [
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
        ]

        rows = sorted(
            self.engine.issues,
            key=lambda item: item["issue_id"]
        )

        self.write_csv("issues.csv", columns, rows)

    # --------------------------------
    # HOLDS REPORT
    # --------------------------------

    def generate_holds_report(self):
        columns = [
            "hold_id",
            "title_id",
            "member_id",
            "placed_ts",
            "status",
            "shelf_copy_id",
            "shelf_expiry_date"
        ]

        rows = sorted(
            self.engine.holds,
            key=lambda item: item["hold_id"]
        )

        self.write_csv("holds.csv", columns, rows)

    # --------------------------------
    # LEDGER REPORT
    # --------------------------------

    def generate_ledger_report(self):
        columns = [
            "member_id",
            "entry_ts",
            "entry_type",
            "reference",
            "amount",
            "balance_after"
        ]

        self.write_csv(
            "member_ledger.csv",
            columns,
            self.engine.ledger
        )

    # --------------------------------
    # CIRCULATION REPORT
    # --------------------------------

    def generate_circulation_report(self):
        columns = [
            "line_no",
            "command",
            "member_id",
            "copy_or_ref",
            "event_ts",
            "result",
            "reason",
            "due_date",
            "charge"
        ]

        self.write_csv(
            "circulation_log.csv",
            columns,
            self.engine.circulation_log
        )

    # --------------------------------
    # MEMBER STATEMENT
    # --------------------------------

    def calculate_member_status(self, member_id, as_of_date):

        member = self.engine.member_state[member_id]

        opening_balance = float(member["opening_balance"])

        outstanding = opening_balance

        for entry in self.engine.ledger:

            if entry["member_id"] != member_id:
                continue

            entry_date = datetime.strptime(
                entry["entry_ts"],
                "%Y-%m-%d %H:%M:%S"
            ).date()

            if entry_date <= as_of_date:
                outstanding += float(entry["amount"])

        outstanding = round(max(0, outstanding), 2)

        active_issues = []

        for issue in self.engine.issues:

            if issue["member_id"] != member_id:
                continue

            if issue["issue_date"] > as_of_date:
                continue

            return_date = issue["return_date"]

            if return_date:
                if return_date <= as_of_date:
                    continue

            active_issues.append(issue)

        max_overdue_days = 0

        for issue in active_issues:

            due_date = issue["current_due_date"]

            overdue_days = self.engine.count_open_days_after(
                due_date,
                as_of_date
            )

            max_overdue_days = max(
                max_overdue_days,
                overdue_days
            )

        reasons = []

        if outstanding > 200:
            reasons.append("FINANCIAL_BLOCK")

        if max_overdue_days > 30:
            reasons.append("OVERDUE_BLOCK")

        expiry_date = self.engine.parse_date(
            member["membership_expiry"]
        )

        if expiry_date < as_of_date:
            reasons.append("MEMBERSHIP_EXPIRED")

        block_status = "BLOCKED" if reasons else "CLEAR"

        return {
            "member_id": member_id,
            "as_of_date": as_of_date,
            "items_on_loan": len(active_issues),
            "outstanding": outstanding,
            "max_overdue_days": max_overdue_days,
            "block_status": block_status,
            "block_reasons": ";".join(reasons)
        }

    def process_statements(self):

        for command in self.engine.commands:

            parts = command["parts"]

            if parts[0] != "PRINT_STATEMENT":
                continue

            if len(parts) != 3:
                print(
                    "Invalid PRINT_STATEMENT command:",
                    parts
                )
                continue

            _, member_id, date_text = parts

            if member_id not in self.engine.member_state:
                print("Invalid statement member:", member_id)
                continue

            as_of_date = self.engine.parse_date(date_text)

            status = self.calculate_member_status(
                member_id,
                as_of_date
            )

            self.member_status_rows.append(status)

            print(
                f"Statement processed: {member_id} "
                f"({date_text})"
            )

    def generate_member_status_report(self):

        columns = [
            "member_id",
            "as_of_date",
            "items_on_loan",
            "outstanding",
            "max_overdue_days",
            "block_status",
            "block_reasons"
        ]

        self.write_csv(
            "member_status.csv",
            columns,
            self.member_status_rows
        )

    # --------------------------------
    # DAILY SUMMARY
    # --------------------------------

    def process_daily_summaries(self):

        print("\nDAILY SUMMARIES")
        print("---------------")

        for command in self.engine.commands:

            parts = command["parts"]

            if parts[0] != "PRINT_DAILY_SUMMARY":
                continue

            if len(parts) != 2:
                continue

            report_date = self.engine.parse_date(parts[1])

            daily_records = [
                record
                for record in self.engine.circulation_log
                if datetime.strptime(
                    record["event_ts"],
                    "%Y-%m-%d %H:%M:%S"
                ).date() == report_date
            ]

            print("\nDate:", report_date)

            for operation in [
                "ISSUE",
                "RETURN",
                "RENEW",
                "HOLD",
                "INSPECT"
            ]:

                successful = sum(
                    1 for record in daily_records
                    if record["command"] == operation
                    and record["result"] == "OK"
                )

                rejected = sum(
                    1 for record in daily_records
                    if record["command"] == operation
                    and record["result"] == "REJECTED"
                )

                print(
                    operation,
                    "- Successful:",
                    successful,
                    "| Rejected:",
                    rejected
                )

    # --------------------------------
    # OVERDUE REPORT
    # --------------------------------

    def process_overdue_reports(self):

        print("\nOVERDUE REPORTS")
        print("---------------")

        for command in self.engine.commands:

            parts = command["parts"]

            if parts[0] != "PRINT_OVERDUE":
                continue

            if len(parts) != 2:
                continue

            report_date = self.engine.parse_date(parts[1])

            print("\nOverdue as of:", report_date)

            found = False

            for issue in self.engine.issues:

                if issue["issue_date"] > report_date:
                    continue

                if issue["return_date"]:
                    if issue["return_date"] <= report_date:
                        continue

                overdue_days = self.engine.count_open_days_after(
                    issue["current_due_date"],
                    report_date
                )

                if overdue_days > 0:

                    found = True

                    print(
                        issue["issue_id"],
                        "| Member:",
                        issue["member_id"],
                        "| Due:",
                        issue["current_due_date"],
                        "| Overdue open days:",
                        overdue_days
                    )

            if not found:
                print("No overdue items.")

    # --------------------------------
    # HOLD QUEUE REPORT
    # --------------------------------

    def process_hold_queue_reports(self):

        print("\nHOLD QUEUE REPORTS")
        print("------------------")

        for command in self.engine.commands:

            parts = command["parts"]

            if parts[0] != "PRINT_HOLD_QUEUE":
                continue

            if len(parts) != 3:
                continue

            _, title_id, date_text = parts

            report_date = self.engine.parse_date(date_text)

            print("\nTitle:", title_id)
            print("As of:", report_date)

            queue = [
                hold
                for hold in self.engine.holds
                if hold["title_id"] == title_id
                and hold["status"] in {
                    "PENDING",
                    "ON_HOLD_SHELF"
                }
                and hold["placed_ts"].date() <= report_date
            ]

            queue.sort(
                key=self.engine.get_hold_priority
            )

            if not queue:
                print("No active holds.")
                continue

            for position, hold in enumerate(queue, start=1):

                print(
                    position,
                    "|",
                    hold["hold_id"],
                    "| Member:",
                    hold["member_id"],
                    "| Status:",
                    hold["status"]
                )

    # --------------------------------
    # GENERATE ALL REPORTS
    # --------------------------------

    def generate_all_reports(self):

        print("\nPROCESSING PRINT COMMANDS")
        print("-------------------------")

        self.process_statements()
        self.process_daily_summaries()
        self.process_overdue_reports()
        self.process_hold_queue_reports()

        print("\nGENERATING CSV REPORTS")
        print("----------------------")

        self.generate_issues_report()
        self.generate_holds_report()
        self.generate_ledger_report()
        self.generate_circulation_report()
        self.generate_member_status_report()

        print("\nAll five CSV report files generated successfully.")


if __name__ == "__main__":

    engine = LibraryEngine()

    engine.run()

    reports = ReportGenerator(engine)

    reports.generate_all_reports()