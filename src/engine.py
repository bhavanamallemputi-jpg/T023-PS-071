import csv
from pathlib import Path
from datetime import datetime, timedelta


class LibraryEngine:

    LOAN_LIMITS = {
        "UG": 3,
        "PG": 5,
        "RESEARCH": 8,
        "FACULTY": 10,
        "EXTERNAL": 2
    }

    LOAN_PERIODS = {
        "UG": 14,
        "PG": 21,
        "RESEARCH": 30,
        "FACULTY": 90,
        "EXTERNAL": 7
    }

    SPECIAL_CATEGORIES = {"JOURNAL", "DVD"}
    REFERENCE_CATEGORIES = {"REFERENCE", "THESIS"}

    HOLD_PRIORITY = {
        "FACULTY": 0,
        "RESEARCH": 1
    }

    def __init__(self):
        self.project_dir = Path(__file__).resolve().parent.parent
        self.data_dir = self.project_dir / "data"
        self.output_dir = self.project_dir / "output"

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.members = self.load_csv("members.csv")
        self.titles = self.load_csv("titles.csv")
        self.copies = self.load_csv("copies.csv")
        self.partners = self.load_csv("partners.csv")
        self.partner_holdings = self.load_csv("partner_holdings.csv")
        self.closed_days_data = self.load_csv("closed_days.csv")

        self.member_map = {
            row["member_id"]: row for row in self.members
        }

        self.title_map = {
            row["title_id"]: row for row in self.titles
        }

        self.copy_map = {
            row["copy_id"]: row for row in self.copies
        }

        self.partner_map = {
            row["partner_id"]: row for row in self.partners
        }

        self.closed_days = {
            datetime.strptime(
                row["closed_date"], "%Y-%m-%d"
            ).date()
            for row in self.closed_days_data
        }

        self.commands = self.load_commands()

        self.issues = []
        self.holds = []
        self.ledger = []
        self.circulation_log = []
        self.member_status = []

        self.ill_requests = {}

        # Outstanding charges, maintained in chronological order.
        self.charge_queue = []

        self.copy_state = {
            row["copy_id"]: {
                **row,
                "status": "AVAILABLE",
                "member_id": None,
                "issue_date": None,
                "due_date": None,
                "renewals": 0,
                "recalled": False,
                "shelf_member_id": None,
                "lost_date": None
            }
            for row in self.copies
        }

        self.member_state = {
            row["member_id"]: {
                **row,
                "outstanding": round(
                    float(row["opening_balance"]), 2
                ),
                "active_loans": 0,
                "total_fines": 0.0
            }
            for row in self.members
        }

        # Opening balances are the oldest outstanding charges.
        for member in self.members:
            opening_balance = round(
                float(member["opening_balance"]), 2
            )

            if opening_balance > 0:
                self.charge_queue.append({
                    "member_id": member["member_id"],
                    "reference": "OPENING_BALANCE",
                    "entry_type": "OPENING_BALANCE",
                    "original_amount": opening_balance,
                    "remaining": opening_balance,
                    "issue_id": None,
                    "waiver_eligible": False
                })

        self.issue_counter = 0
        self.hold_counter = 0
        self.last_processed_date = None

    # -------------------------------
    # FILE HANDLING
    # -------------------------------

    def load_csv(self, filename):
        file_path = self.data_dir / filename

        with open(
            file_path,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:
            return list(csv.DictReader(file))

    def load_commands(self):
        file_path = self.data_dir / "commands.txt"
        commands = []

        with open(file_path, "r", encoding="utf-8-sig") as file:
            for line_no, line in enumerate(file, start=1):
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                commands.append({
                    "line_no": line_no,
                    "parts": line.split("|")
                })

        return commands

    # -------------------------------
    # DATE HANDLING
    # -------------------------------

    @staticmethod
    def parse_date(value):
        return datetime.strptime(value, "%Y-%m-%d").date()

    @staticmethod
    def parse_timestamp(value):
        return datetime.strptime(
            value, "%Y-%m-%d %H:%M:%S"
        )

    def next_open_day(self, day):
        while day in self.closed_days:
            day += timedelta(days=1)

        return day

    def add_open_days(self, start_date, number_of_days):
        current_date = start_date
        added_days = 0

        while added_days < number_of_days:
            current_date += timedelta(days=1)

            if current_date not in self.closed_days:
                added_days += 1

        return current_date

    def count_open_days_after(self, start_date, end_date):
        count = 0
        current_day = start_date + timedelta(days=1)

        while current_day <= end_date:
            if current_day not in self.closed_days:
                count += 1

            current_day += timedelta(days=1)

        return count

    # -------------------------------
    # LOAN RULES
    # -------------------------------

    def get_loan_period(self, member, title):
        category = title["category"].upper()
        member_category = member["category"].upper()

        if category in self.SPECIAL_CATEGORIES:
            return 7

        if category in self.REFERENCE_CATEGORIES:
            if member_category == "FACULTY":
                return 2
            return None

        return self.LOAN_PERIODS.get(member_category)

    def get_loan_limit(self, member):
        return self.LOAN_LIMITS.get(
            member["category"].upper(), 0
        )

    def count_reference_loans(self, member_id):
        return sum(
            1 for issue in self.issues
            if issue["member_id"] == member_id
            and issue["status"] == "ISSUED"
            and issue.get("category") in self.REFERENCE_CATEGORIES
        )

    # -------------------------------
    # LEDGER AND CHARGE MANAGEMENT
    # -------------------------------

    def add_charge(
        self,
        member_id,
        timestamp,
        entry_type,
        reference,
        amount,
        issue_id=None,
        waiver_eligible=False
    ):
        amount = round(float(amount), 2)

        if amount <= 0:
            return

        member = self.member_state[member_id]

        member["outstanding"] = round(
            member["outstanding"] + amount, 2
        )

        member["total_fines"] = round(
            member["total_fines"] + amount, 2
        )

        self.ledger.append({
            "member_id": member_id,
            "entry_ts": timestamp,
            "entry_type": entry_type,
            "reference": reference,
            "amount": amount,
            "balance_after": member["outstanding"]
        })

        self.charge_queue.append({
            "member_id": member_id,
            "reference": reference,
            "entry_type": entry_type,
            "original_amount": amount,
            "remaining": amount,
            "issue_id": issue_id,
            "waiver_eligible": waiver_eligible
        })

    def reduce_charge_queue(self, member_id, amount, issue_id=None):
        remaining_amount = round(float(amount), 2)

        for charge in self.charge_queue:

            if charge["member_id"] != member_id:
                continue

            if issue_id is not None:
                if charge["issue_id"] != issue_id:
                    continue

            if charge["remaining"] <= 0:
                continue

            deduction = min(
                charge["remaining"],
                remaining_amount
            )

            charge["remaining"] = round(
                charge["remaining"] - deduction, 2
            )

            remaining_amount = round(
                remaining_amount - deduction, 2
            )

            if remaining_amount <= 0:
                break

        return round(remaining_amount, 2)

    # -------------------------------
    # LOGGING
    # -------------------------------

    def log_result(
        self,
        command,
        member_id,
        copy_id,
        event_ts,
        result,
        reason="",
        due_date="",
        charge=0
    ):
        self.circulation_log.append({
            "line_no": command["line_no"],
            "command": command["parts"][0],
            "member_id": member_id,
            "copy_or_ref": copy_id,
            "event_ts": event_ts,
            "result": result,
            "reason": reason,
            "due_date": due_date,
            "charge": charge
        })

    def find_active_issue(self, copy_id):
        for issue in reversed(self.issues):
            if (
                issue["copy_or_ill_id"] == copy_id
                and issue["status"] == "ISSUED"
            ):
                return issue

        return None

    # -------------------------------
    # HOLD QUEUE HELPERS
    # -------------------------------

    def get_active_holds(self, title_id):
        return [
            hold for hold in self.holds
            if hold["title_id"] == title_id
            and hold["status"] in {
                "PENDING",
                "ON_HOLD_SHELF"
            }
        ]

    def get_hold_priority(self, hold):
        member = self.member_state[hold["member_id"]]

        priority = self.HOLD_PRIORITY.get(
            member["category"].upper(), 2
        )

        return priority, hold["placed_ts"], hold["hold_id"]

    def get_next_pending_hold(self, title_id):
        pending = [
            hold for hold in self.get_active_holds(title_id)
            if hold["status"] == "PENDING"
        ]

        if not pending:
            return None

        pending.sort(key=self.get_hold_priority)

        return pending[0]

    def member_has_title_on_loan(self, member_id, title_id):
        return any(
            issue["member_id"] == member_id
            and issue["status"] == "ISSUED"
            and self.copy_state.get(
                issue["copy_or_ill_id"], {}
            ).get("title_id") == title_id
            for issue in self.issues
        )

    def count_member_holds(self, member_id):
        return sum(
            1 for hold in self.holds
            if hold["member_id"] == member_id
            and hold["status"] in {
                "PENDING",
                "ON_HOLD_SHELF"
            }
        )

    def member_has_active_hold(self, member_id, title_id):
        return any(
            hold["member_id"] == member_id
            and hold["title_id"] == title_id
            and hold["status"] in {
                "PENDING",
                "ON_HOLD_SHELF"
            }
            for hold in self.holds
        )

    def assign_copy_to_hold(self, copy, event_date):
        title_id = copy["title_id"]

        next_hold = self.get_next_pending_hold(title_id)

        if next_hold is None:
            copy["status"] = "AVAILABLE"
            copy["shelf_member_id"] = None
            return

        next_hold["status"] = "ON_HOLD_SHELF"

        copy["status"] = "ON_HOLD_SHELF"
        copy["shelf_member_id"] = next_hold["member_id"]

        next_hold["shelf_copy_id"] = copy["copy_id"]
        next_hold["shelf_expiry_date"] = (
            self.add_open_days(event_date, 3)
        )

    # -------------------------------
    # DAILY LIFECYCLE: LOST BOOKS + HOLD EXPIRY
    # -------------------------------

    def process_daily_events(self, event_date):
        """
        Run once at the start of each calendar day.
        A physical book becomes LOST on day 61 after its due date.
        """
        for copy in self.copy_state.values():
            if copy["status"] != "ISSUED" or copy.get("member_id") is None:
                continue

            issue = self.find_active_issue(copy["copy_id"])
            if issue is None or issue.get("is_ill", False):
                continue

            due_date = issue["current_due_date"]
            lost_date = due_date + timedelta(days=61)

            if event_date < lost_date:
                continue

            member_id = issue["member_id"]
            price = round(float(copy["price"]), 2)
            fine_end_date = due_date + timedelta(days=60)
            fine = self.calculate_fine(issue, fine_end_date, price)
            processing_fee = 100.00

            issue["status"] = "LOST"
            issue["lost_date"] = event_date
            issue["lost_fine"] = fine
            issue["lost_replacement_price"] = price
            issue["lost_processing_fee"] = processing_fee

            member = self.member_state[member_id]
            member["active_loans"] = max(0, member["active_loans"] - 1)

            # Keep replacement, processing fee, and fine separate so the
            # replacement price can be refunded if the book is returned.
            self.add_charge(
                member_id, event_date.isoformat() + " 00:00:00",
                "LOST_REPLACEMENT", issue["issue_id"], price,
                issue_id=issue["issue_id"], waiver_eligible=False
            )
            self.add_charge(
                member_id, event_date.isoformat() + " 00:00:00",
                "LOST_PROCESSING", issue["issue_id"], processing_fee,
                issue_id=issue["issue_id"], waiver_eligible=False
            )
            if fine > 0:
                self.add_charge(
                    member_id, event_date.isoformat() + " 00:00:00",
                    "LOST_FINE", issue["issue_id"], fine,
                    issue_id=issue["issue_id"], waiver_eligible=True
                )

            copy["status"] = "LOST"
            copy["lost_date"] = event_date
            copy["member_id"] = None
            copy["issue_date"] = None
            copy["due_date"] = None
            copy["renewals"] = 0
            copy["recalled"] = False
            copy["shelf_member_id"] = None

        # Expire uncollected holds after three open days.
        for hold in self.holds:
            if hold["status"] != "ON_HOLD_SHELF":
                continue
            expiry = hold.get("shelf_expiry_date")
            if expiry and event_date > expiry:
                hold["status"] = "EXPIRED"
                copy = self.copy_state.get(hold.get("shelf_copy_id"))
                if copy and copy["status"] == "ON_HOLD_SHELF":
                    copy["status"] = "AVAILABLE"
                    copy["shelf_member_id"] = None
                    copy["lost_date"] = None
                    self.assign_copy_to_hold(copy, event_date)

    def process_daily_events_until(self, target_date):
        if self.last_processed_date is None:
            self.last_processed_date = target_date - timedelta(days=1)

        current = self.last_processed_date + timedelta(days=1)
        while current <= target_date:
            self.process_daily_events(current)
            self.last_processed_date = current
            current += timedelta(days=1)

    @staticmethod
    def command_event_date(command):
        parts = command["parts"]
        operation = parts[0]
        if operation in {"PRINT_DAILY_SUMMARY", "PRINT_OVERDUE"} and len(parts) >= 2:
            return LibraryEngine.parse_date(parts[1])
        if operation in {"PRINT_STATEMENT", "PRINT_HOLD_QUEUE"} and len(parts) >= 3:
            return LibraryEngine.parse_date(parts[2])
        if len(parts) >= 2:
            value = parts[-1]
            try:
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").date()
            except ValueError:
                try:
                    return LibraryEngine.parse_date(value)
                except ValueError:
                    return None
        return None

    # -------------------------------
    # ISSUE OPERATION
    # -------------------------------

    def issue_book(self, command):
        parts = command["parts"]

        if len(parts) != 4:
            self.log_result(
                command, "", "", "",
                "REJECTED", "INVALID_COMMAND"
            )
            return False

        _, member_id, copy_id, timestamp = parts

        event_time = self.parse_timestamp(timestamp)
        issue_date = event_time.date()

        member = self.member_state.get(member_id)
        copy = self.copy_state.get(copy_id)

        if member is None or copy is None:
            self.log_result(
                command, member_id, copy_id,
                timestamp, "REJECTED", "INVALID_MEMBER_OR_COPY"
            )
            return False

        title = self.title_map.get(copy["title_id"])

        if title is None:
            self.log_result(
                command, member_id, copy_id,
                timestamp, "REJECTED", "NOT_ISSUABLE"
            )
            return False

        if self.parse_date(member["membership_expiry"]) < issue_date:
            self.log_result(
                command, member_id, copy_id,
                timestamp, "REJECTED", "EXPIRED"
            )
            return False

        if member["standing"].upper() != "GOOD":
            self.log_result(
                command, member_id, copy_id,
                timestamp, "REJECTED", "BLOCKED"
            )
            return False

        if member["outstanding"] > 200:
            self.log_result(
                command, member_id, copy_id,
                timestamp, "REJECTED", "BLOCKED"
            )
            return False

        loan_period = self.get_loan_period(member, title)

        if loan_period is None:
            self.log_result(
                command, member_id, copy_id,
                timestamp, "REJECTED", "NOT_ISSUABLE"
            )
            return False

        if copy["status"] == "ON_HOLD_SHELF":
            if copy["shelf_member_id"] != member_id:
                self.log_result(
                    command, member_id, copy_id,
                    timestamp, "REJECTED", "BLOCKED"
                )
                return False

        elif copy["status"] != "AVAILABLE":
            self.log_result(
                command, member_id, copy_id,
                timestamp, "REJECTED", "COPIES_AVAILABLE"
            )
            return False

        if member["active_loans"] >= self.get_loan_limit(member):
            self.log_result(
                command, member_id, copy_id,
                timestamp, "REJECTED", "LIMIT"
            )
            return False

        if (
            title["category"].upper() in self.REFERENCE_CATEGORIES
            and self.count_reference_loans(member_id) >= 2
        ):
            self.log_result(
                command, member_id, copy_id,
                timestamp, "REJECTED", "LIMIT"
            )
            return False

        due_date = self.next_open_day(
            issue_date + timedelta(days=loan_period)
        )

        self.issue_counter += 1
        issue_id = f"ISS-{self.issue_counter:05d}"

        if copy["status"] == "ON_HOLD_SHELF":
            for hold in self.holds:
                if (
                    hold["status"] == "ON_HOLD_SHELF"
                    and hold["shelf_copy_id"] == copy_id
                    and hold["member_id"] == member_id
                ):
                    hold["status"] = "COLLECTED"

        copy["status"] = "ISSUED"
        copy["member_id"] = member_id
        copy["issue_date"] = issue_date
        copy["due_date"] = due_date
        copy["shelf_member_id"] = None
        copy["renewals"] = 0

        member["active_loans"] += 1

        self.issues.append({
            "issue_id": issue_id,
            "member_id": member_id,
            "copy_or_ill_id": copy_id,
            "issue_date": issue_date,
            "original_due_date": due_date,
            "current_due_date": due_date,
            "renewals": 0,
            "recalled": False,
            "return_date": "",
            "status": "ISSUED",
            "fine": 0.0,
            "waived": 0.0,
            "category": title["category"].upper(),
            "is_ill": False
        })

        self.log_result(
            command,
            member_id,
            copy_id,
            timestamp,
            "OK",
            "",
            due_date.isoformat(),
            0
        )

        return True

    # -------------------------------
    # FINE CALCULATION
    # -------------------------------

    def calculate_fine(self, issue, return_date, item_price):
        due_date = issue["current_due_date"]
        category = issue["category"]

        overdue_days = self.count_open_days_after(
            due_date, return_date
        )

        if issue.get("is_ill", False):
            fine = overdue_days * 20

        elif category in self.SPECIAL_CATEGORIES:
            fine = overdue_days * 10

        else:
            chargeable_days = max(0, overdue_days - 1)

            first_seven = min(chargeable_days, 7)
            remaining_days = max(0, chargeable_days - 7)

            fine = first_seven * 2 + remaining_days * 5

        if issue["recalled"]:
            fine *= 2

        if issue.get("is_ill", False):
            return round(fine, 2)

        return round(min(fine, 500, float(item_price)), 2)

    # -------------------------------
    # RETURN OPERATION
    # -------------------------------

    def return_book(self, command):
        parts = command["parts"]

        if len(parts) != 3:
            self.log_result(
                command, "", "", "",
                "REJECTED", "INVALID_COMMAND"
            )
            return False

        _, copy_id, timestamp = parts

        return_time = self.parse_timestamp(timestamp)
        return_date = return_time.date()

        copy = self.copy_state.get(copy_id)

        if copy is None or copy["status"] not in {"ISSUED", "LOST"}:
            self.log_result(
                command, "", copy_id,
                timestamp, "REJECTED", "NOT_ON_LOAN"
            )
            return False

        if copy["status"] == "LOST":
            lost_issue = next(
                (
                    item for item in reversed(self.issues)
                    if item["copy_or_ill_id"] == copy_id
                    and item["status"] == "LOST"
                ),
                None
            )
            if lost_issue is None:
                self.log_result(
                    command, "", copy_id,
                    timestamp, "REJECTED", "NOT_ON_LOAN"
                )
                return False

            lost_date = lost_issue.get("lost_date")
            if lost_date and return_date <= lost_date + timedelta(days=30):
                member_id = lost_issue["member_id"]
                replacement_charge = next(
                    (
                        charge for charge in self.charge_queue
                        if charge["issue_id"] == lost_issue["issue_id"]
                        and charge["entry_type"] == "LOST_REPLACEMENT"
                    ),
                    None
                )
                if replacement_charge is not None:
                    unpaid_replacement = round(replacement_charge["remaining"], 2)
                    paid_replacement = round(
                        max(0.0, float(copy["price"]) - unpaid_replacement), 2
                    )
                    replacement_charge["remaining"] = 0.0
                    member = self.member_state[member_id]
                    member["outstanding"] = round(
                        member["outstanding"] - unpaid_replacement, 2
                    )
                    if paid_replacement > 0:
                        member["outstanding"] = round(
                            member["outstanding"] - paid_replacement, 2
                        )
                    self.ledger.append({
                        "member_id": member_id,
                        "entry_ts": timestamp,
                        "entry_type": "LOST_ITEM_REFUND",
                        "reference": lost_issue["issue_id"],
                        "amount": -float(copy["price"]),
                        "balance_after": member["outstanding"]
                    })

                lost_issue["status"] = "RETURNED_AFTER_LOST"
                lost_issue["return_date"] = return_date
                lost_issue["replacement_refunded"] = True
                copy["lost_date"] = None
                self.assign_copy_to_hold(copy, return_date)
                self.log_result(
                    command, member_id, copy_id, timestamp,
                    "OK", "LOST_ITEM_RETURNED_REPLACEMENT_REFUNDED",
                    "", -float(copy["price"])
                )
                return True

            self.log_result(
                command, lost_issue["member_id"], copy_id,
                timestamp, "REJECTED", "LOST_RETURN_WINDOW_EXPIRED"
            )
            return False

        issue = self.find_active_issue(copy_id)

        if issue is None:
            self.log_result(
                command, copy["member_id"], copy_id,
                timestamp, "REJECTED", "NOT_ON_LOAN"
            )
            return False

        member_id = issue["member_id"]

        fine = self.calculate_fine(
            issue,
            return_date,
            copy["price"]
        )

        issue["return_date"] = return_date
        issue["status"] = "RETURNED"
        issue["fine"] = fine

        member = self.member_state[member_id]

        member["active_loans"] = max(
            0, member["active_loans"] - 1
        )

        if fine > 0:
            self.add_charge(
                member_id,
                timestamp,
                "FINE",
                issue["issue_id"],
                fine,
                issue_id=issue["issue_id"],
                waiver_eligible=True
            )

        copy["member_id"] = None
        copy["issue_date"] = None
        copy["due_date"] = None
        copy["renewals"] = 0
        copy["recalled"] = False
        copy["shelf_member_id"] = None

        self.assign_copy_to_hold(copy, return_date)

        self.log_result(
            command,
            member_id,
            copy_id,
            timestamp,
            "OK",
            "",
            "",
            fine
        )

        return True

    # -------------------------------
    # RENEW OPERATION
    # -------------------------------

    def renew_book(self, command):
        parts = command["parts"]

        if len(parts) != 4:
            self.log_result(
                command, "", "", "",
                "REJECTED", "INVALID_COMMAND"
            )
            return False

        _, member_id, copy_id, timestamp = parts

        renewal_time = self.parse_timestamp(timestamp)
        renewal_date = renewal_time.date()

        copy = self.copy_state.get(copy_id)

        if copy is None or copy["status"] != "ISSUED":
            self.log_result(
                command, member_id, copy_id,
                timestamp, "REJECTED", "NOT_ON_LOAN"
            )
            return False

        issue = self.find_active_issue(copy_id)

        if issue is None or issue["member_id"] != member_id:
            self.log_result(
                command, member_id, copy_id,
                timestamp, "REJECTED", "NOT_ON_LOAN"
            )
            return False

        if issue.get("is_ill", False):
            self.log_result(
                command, member_id, copy_id,
                timestamp, "REJECTED", "NOT_ON_LOAN"
            )
            return False

        current_due_date = issue["current_due_date"]

        if renewal_date > current_due_date:
            self.log_result(
                command, member_id, copy_id,
                timestamp, "REJECTED", "OVERDUE"
            )
            return False

        if renewal_date < current_due_date - timedelta(days=2):
            self.log_result(
                command, member_id, copy_id,
                timestamp, "REJECTED", "REJECTED_EARLY"
            )
            return False

        if issue["renewals"] >= 2:
            self.log_result(
                command, member_id, copy_id,
                timestamp, "REJECTED", "MAX_RENEWALS"
            )
            return False

        title_id = copy["title_id"]

        if any(
            hold["title_id"] == title_id
            and hold["status"] in {"PENDING", "ON_HOLD_SHELF"}
            and hold["member_id"] != member_id
            for hold in self.holds
        ):
            self.log_result(
                command, member_id, copy_id,
                timestamp, "REJECTED", "HOLD_EXISTS"
            )
            return False

        title = self.title_map[title_id]
        member = self.member_state[member_id]

        loan_period = self.get_loan_period(member, title)

        if loan_period is None:
            self.log_result(
                command, member_id, copy_id,
                timestamp, "REJECTED", "NOT_ON_LOAN"
            )
            return False

        new_due_date = self.next_open_day(
            current_due_date + timedelta(days=loan_period)
        )

        issue["renewals"] += 1
        issue["current_due_date"] = new_due_date

        copy["due_date"] = new_due_date
        copy["renewals"] = issue["renewals"]

        self.log_result(
            command,
            member_id,
            copy_id,
            timestamp,
            "OK",
            "",
            new_due_date.isoformat(),
            0
        )

        return True

    # -------------------------------
    # HOLD OPERATION
    # -------------------------------

    def place_hold(self, command):
        parts = command["parts"]

        if len(parts) != 4:
            self.log_result(
                command, "", "", "",
                "REJECTED", "INVALID_COMMAND"
            )
            return False

        _, member_id, title_id, timestamp = parts

        event_time = self.parse_timestamp(timestamp)
        event_date = event_time.date()

        member = self.member_state.get(member_id)
        title = self.title_map.get(title_id)

        if member is None or title is None:
            self.log_result(
                command, member_id, title_id,
                timestamp, "REJECTED", "INVALID_COMMAND"
            )
            return False

        if self.parse_date(member["membership_expiry"]) < event_date:
            self.log_result(
                command, member_id, title_id,
                timestamp, "REJECTED", "EXPIRED"
            )
            return False

        if member["standing"].upper() != "GOOD":
            self.log_result(
                command, member_id, title_id,
                timestamp, "REJECTED", "BLOCKED"
            )
            return False

        if member["outstanding"] > 200:
            self.log_result(
                command, member_id, title_id,
                timestamp, "REJECTED", "BLOCKED"
            )
            return False

        if self.member_has_title_on_loan(member_id, title_id):
            self.log_result(
                command, member_id, title_id,
                timestamp, "REJECTED", "ON_LOAN_TO_MEMBER"
            )
            return False

        if self.member_has_active_hold(member_id, title_id):
            self.log_result(
                command, member_id, title_id,
                timestamp, "REJECTED", "HOLD_EXISTS"
            )
            return False

        if self.count_member_holds(member_id) >= 3:
            self.log_result(
                command, member_id, title_id,
                timestamp, "REJECTED", "HOLD_LIMIT"
            )
            return False

        title_copies = [
            copy for copy in self.copy_state.values()
            if copy["title_id"] == title_id
        ]

        if not title_copies:
            self.log_result(
                command, member_id, title_id,
                timestamp, "REJECTED", "NOT_ISSUABLE"
            )
            return False

        if not all(
            copy["status"] == "ISSUED"
            for copy in title_copies
        ):
            self.log_result(
                command, member_id, title_id,
                timestamp, "REJECTED", "COPIES_AVAILABLE"
            )
            return False

        self.hold_counter += 1
        hold_id = f"HLD-{self.hold_counter:04d}"

        self.holds.append({
            "hold_id": hold_id,
            "title_id": title_id,
            "member_id": member_id,
            "placed_ts": event_time,
            "status": "PENDING",
            "shelf_copy_id": "",
            "shelf_expiry_date": ""
        })

        self.log_result(
            command,
            member_id,
            title_id,
            timestamp,
            "OK",
            "",
            "",
            0
        )

        return True

    # -------------------------------
    # INSPECT OPERATION
    # -------------------------------

    def inspect_book(self, command):
        parts = command["parts"]

        if len(parts) != 4:
            self.log_result(
                command, "", "", "",
                "REJECTED", "INVALID_COMMAND"
            )
            return False

        _, copy_id, damage_type, timestamp = parts

        damage_type = damage_type.upper()
        event_time = self.parse_timestamp(timestamp)

        copy = self.copy_state.get(copy_id)

        if copy is None:
            self.log_result(
                command, "", copy_id,
                timestamp, "REJECTED", "NOT_ON_LOAN"
            )
            return False

        if damage_type not in {"MINOR", "MAJOR"}:
            self.log_result(
                command, "", copy_id,
                timestamp, "REJECTED", "INVALID_COMMAND"
            )
            return False

        if copy["status"] in {"DAMAGED", "LOST"}:
            self.log_result(
                command, "", copy_id,
                timestamp, "REJECTED", "NOT_ON_LOAN"
            )
            return False

        member_id = copy.get("member_id")
        issue = None

        if copy["status"] == "ISSUED":
            issue = self.find_active_issue(copy_id)

            if issue is None:
                self.log_result(
                    command, member_id or "", copy_id,
                    timestamp, "REJECTED", "NOT_ON_LOAN"
                )
                return False

        price = float(copy["price"])

        if damage_type == "MINOR":
            charge = price * 0.50
        else:
            charge = price + 100

        if issue is not None:
            issue["status"] = "DAMAGED"
            issue["return_date"] = event_time.date()
            issue["fine"] = charge
            issue["waived"] = 0.0

            member = self.member_state[member_id]

            member["active_loans"] = max(
                0, member["active_loans"] - 1
            )

            self.add_charge(
                member_id,
                timestamp,
                "DAMAGE",
                issue["issue_id"],
                charge,
                issue_id=issue["issue_id"],
                waiver_eligible=False
            )

        copy["status"] = "DAMAGED"
        copy["member_id"] = None
        copy["issue_date"] = None
        copy["due_date"] = None
        copy["renewals"] = 0
        copy["recalled"] = False
        copy["shelf_member_id"] = None

        self.log_result(
            command,
            member_id or "",
            copy_id,
            timestamp,
            "OK",
            "",
            "",
            charge
        )

        return True

    # -------------------------------
    # ILL PARTNER SELECTION
    # -------------------------------

    def find_ill_partner(self, isbn):
        matching_holdings = [
            holding for holding in self.partner_holdings
            if holding["isbn"].strip() == isbn.strip()
        ]

        if not matching_holdings:
            return None

        matching_holdings.sort(
            key=lambda holding: (
                int(
                    self.partner_map[
                        holding["partner_id"]
                    ]["transit_days"]
                ),
                holding["partner_id"]
            )
        )

        selected_holding = matching_holdings[0]

        partner = self.partner_map.get(
            selected_holding["partner_id"]
        )

        if partner is None:
            return None

        return {
            "partner_id": selected_holding["partner_id"],
            "partner_name": partner["partner_name"],
            "transit_days": int(partner["transit_days"]),
            "loan_period_days": int(partner["loan_period_days"]),
            "ill_charge": float(selected_holding["ill_charge"]),
            "replacement_price": float(
                selected_holding["replacement_price"]
            ),
            "isbn": isbn,
            "title": selected_holding["title"]
        }

    # -------------------------------
    # ILL REQUEST OPERATION
    # -------------------------------

    def ill_request(self, command):
        parts = command["parts"]

        if len(parts) != 5:
            self.log_result(
                command, "", "", "",
                "REJECTED", "INVALID_COMMAND"
            )
            return False

        _, ill_id, member_id, isbn, timestamp = parts

        event_time = self.parse_timestamp(timestamp)
        event_date = event_time.date()

        member = self.member_state.get(member_id)

        if member is None:
            self.log_result(
                command, member_id, ill_id,
                timestamp, "REJECTED", "INVALID_MEMBER"
            )
            return False

        if ill_id in self.ill_requests:
            self.log_result(
                command, member_id, ill_id,
                timestamp, "REJECTED", "DUPLICATE_REQUEST"
            )
            return False

        if self.parse_date(member["membership_expiry"]) < event_date:
            self.log_result(
                command, member_id, ill_id,
                timestamp, "REJECTED", "EXPIRED"
            )
            return False

        if member["standing"].upper() != "GOOD":
            self.log_result(
                command, member_id, ill_id,
                timestamp, "REJECTED", "BLOCKED"
            )
            return False

        if member["outstanding"] > 200:
            self.log_result(
                command, member_id, ill_id,
                timestamp, "REJECTED", "BLOCKED"
            )
            return False

        if member["active_loans"] >= self.get_loan_limit(member):
            self.log_result(
                command, member_id, ill_id,
                timestamp, "REJECTED", "LIMIT"
            )
            return False

        partner = self.find_ill_partner(isbn)

        if partner is None:
            self.log_result(
                command, member_id, ill_id,
                timestamp, "REJECTED", "NO_PARTNER_HOLDING"
            )
            return False

        self.ill_requests[ill_id] = {
            "ill_id": ill_id,
            "member_id": member_id,
            "isbn": isbn,
            "request_ts": event_time,
            "status": "REQUESTED",
            **partner
        }

        self.log_result(
            command,
            member_id,
            ill_id,
            timestamp,
            "OK",
            "",
            "",
            0
        )

        return True

    # -------------------------------
    # ILL RECEIVE OPERATION
    # -------------------------------

    def ill_receive(self, command):
        parts = command["parts"]

        if len(parts) != 3:
            self.log_result(
                command, "", "", "",
                "REJECTED", "INVALID_COMMAND"
            )
            return False

        _, ill_id, timestamp = parts

        event_time = self.parse_timestamp(timestamp)
        issue_date = event_time.date()

        request = self.ill_requests.get(ill_id)

        if request is None:
            self.log_result(
                command, "", ill_id,
                timestamp, "REJECTED", "INVALID_REQUEST"
            )
            return False

        if request["status"] != "REQUESTED":
            self.log_result(
                command,
                request["member_id"],
                ill_id,
                timestamp,
                "REJECTED",
                "INVALID_REQUEST"
            )
            return False

        member_id = request["member_id"]
        member = self.member_state[member_id]

        if self.parse_date(member["membership_expiry"]) < issue_date:
            self.log_result(
                command, member_id, ill_id,
                timestamp, "REJECTED", "EXPIRED"
            )
            return False

        if member["standing"].upper() != "GOOD":
            self.log_result(
                command, member_id, ill_id,
                timestamp, "REJECTED", "BLOCKED"
            )
            return False

        if member["outstanding"] > 200:
            self.log_result(
                command, member_id, ill_id,
                timestamp, "REJECTED", "BLOCKED"
            )
            return False

        if member["active_loans"] >= self.get_loan_limit(member):
            self.log_result(
                command, member_id, ill_id,
                timestamp, "REJECTED", "LIMIT"
            )
            return False

        partner_loan_period = request["loan_period_days"]
        transit_days = request["transit_days"]

        member_loan_period = max(
            7,
            partner_loan_period - (2 * transit_days)
        )

        due_date = self.next_open_day(
            issue_date + timedelta(days=member_loan_period)
        )

        self.issue_counter += 1
        issue_id = f"ISS-{self.issue_counter:05d}"

        ill_charge = request["ill_charge"]

        self.issues.append({
            "issue_id": issue_id,
            "member_id": member_id,
            "copy_or_ill_id": ill_id,
            "issue_date": issue_date,
            "original_due_date": due_date,
            "current_due_date": due_date,
            "renewals": 0,
            "recalled": False,
            "return_date": "",
            "status": "ISSUED",
            "fine": 0.0,
            "waived": 0.0,
            "category": "ILL",
            "is_ill": True,
            "partner_id": request["partner_id"],
            "isbn": request["isbn"],
            "ill_charge": ill_charge,
            "replacement_price": request["replacement_price"]
        })

        member["active_loans"] += 1

        self.add_charge(
            member_id,
            timestamp,
            "ILL_CHARGE",
            ill_id,
            ill_charge,
            issue_id=issue_id,
            waiver_eligible=False
        )

        request["status"] = "RECEIVED"
        request["issue_id"] = issue_id
        request["issue_date"] = issue_date
        request["due_date"] = due_date

        self.log_result(
            command,
            member_id,
            ill_id,
            timestamp,
            "OK",
            "",
            due_date.isoformat(),
            ill_charge
        )

        return True

    # -------------------------------
    # ILL RETURN OPERATION
    # -------------------------------

    def ill_return(self, command):
        parts = command["parts"]

        if len(parts) != 3:
            self.log_result(
                command, "", "", "",
                "REJECTED", "INVALID_COMMAND"
            )
            return False

        _, ill_id, timestamp = parts

        return_time = self.parse_timestamp(timestamp)
        return_date = return_time.date()

        request = self.ill_requests.get(ill_id)

        if request is None or request["status"] != "RECEIVED":
            self.log_result(
                command, "", ill_id,
                timestamp, "REJECTED", "NOT_ON_LOAN"
            )
            return False

        issue = self.find_active_issue(ill_id)

        if issue is None:
            self.log_result(
                command,
                request["member_id"],
                ill_id,
                timestamp,
                "REJECTED",
                "NOT_ON_LOAN"
            )
            return False

        member_id = issue["member_id"]

        overdue_days = self.count_open_days_after(
            issue["current_due_date"],
            return_date
        )

        fine = overdue_days * 20

        issue["return_date"] = return_date
        issue["status"] = "RETURNED"
        issue["fine"] = fine

        member = self.member_state[member_id]

        member["active_loans"] = max(
            0, member["active_loans"] - 1
        )

        if fine > 0:
            self.add_charge(
                member_id,
                timestamp,
                "FINE",
                issue["issue_id"],
                fine,
                issue_id=issue["issue_id"],
                waiver_eligible=True
            )

        request["status"] = "RETURNED"
        request["return_date"] = return_date
        request["fine"] = fine

        self.log_result(
            command,
            member_id,
            ill_id,
            timestamp,
            "OK",
            "",
            "",
            fine
        )

        return True

    # -------------------------------
    # PAY OPERATION
    # -------------------------------

    def pay_fine(self, command):
        parts = command["parts"]

        if len(parts) != 4:
            self.log_result(
                command, "", "", "",
                "REJECTED", "INVALID_COMMAND"
            )
            return False

        _, member_id, amount_text, timestamp = parts

        member = self.member_state.get(member_id)

        if member is None:
            self.log_result(
                command, member_id, "",
                timestamp, "REJECTED", "INVALID_MEMBER"
            )
            return False

        try:
            amount = round(float(amount_text), 2)
        except ValueError:
            self.log_result(
                command, member_id, "",
                timestamp, "REJECTED", "INVALID_AMOUNT"
            )
            return False

        if amount <= 0:
            self.log_result(
                command, member_id, "",
                timestamp, "REJECTED", "INVALID_AMOUNT"
            )
            return False

        if amount > member["outstanding"]:
            self.log_result(
                command, member_id, "",
                timestamp, "REJECTED", "OVERPAYMENT"
            )
            return False

        # Apply payment to the oldest outstanding charges first.
        unpaid_amount = self.reduce_charge_queue(
            member_id, amount
        )

        if unpaid_amount > 0:
            self.log_result(
                command, member_id, "",
                timestamp, "REJECTED", "CHARGE_ALLOCATION_ERROR"
            )
            return False

        member["outstanding"] = round(
            max(0, member["outstanding"] - amount), 2
        )

        self.ledger.append({
            "member_id": member_id,
            "entry_ts": timestamp,
            "entry_type": "PAYMENT",
            "reference": "PAYMENT",
            "amount": -amount,
            "balance_after": member["outstanding"]
        })

        self.log_result(
            command,
            member_id,
            "",
            timestamp,
            "OK",
            "",
            "",
            -amount
        )

        return True

    # -------------------------------
    # WAIVE OPERATION
    # -------------------------------

    def waive_fine(self, command):
        parts = command["parts"]

        if len(parts) != 5:
            self.log_result(
                command, "", "", "",
                "REJECTED", "INVALID_COMMAND"
            )
            return False

        _, member_id, issue_id, amount_text, timestamp = parts

        member = self.member_state.get(member_id)

        if member is None:
            self.log_result(
                command, member_id, issue_id,
                timestamp, "REJECTED", "INVALID_MEMBER"
            )
            return False

        try:
            amount = round(float(amount_text), 2)
        except ValueError:
            self.log_result(
                command, member_id, issue_id,
                timestamp, "REJECTED", "INVALID_AMOUNT"
            )
            return False

        if amount <= 0:
            self.log_result(
                command, member_id, issue_id,
                timestamp, "REJECTED", "INVALID_AMOUNT"
            )
            return False

        issue = next(
            (
                item for item in self.issues
                if item["issue_id"] == issue_id
                and item["member_id"] == member_id
            ),
            None
        )

        if issue is None:
            self.log_result(
                command, member_id, issue_id,
                timestamp, "REJECTED", "INVALID_ISSUE"
            )
            return False

        if issue["status"] not in {"RETURNED"}:
            self.log_result(
                command, member_id, issue_id,
                timestamp, "REJECTED", "FINE_NOT_FINALIZED"
            )
            return False

        original_fine = round(float(issue["fine"]), 2)

        if original_fine <= 0:
            self.log_result(
                command, member_id, issue_id,
                timestamp, "REJECTED", "NO_FINE"
            )
            return False

        # Waiver is limited to 50% of the original fine.
        maximum_waiver = round(original_fine * 0.50, 2)

        already_waived = round(
            float(issue.get("waived", 0.0)), 2
        )

        remaining_waiver_limit = round(
            maximum_waiver - already_waived, 2
        )

        # Find the unpaid eligible fine for this issue.
        eligible_charge = None

        for charge in self.charge_queue:
            if (
                charge["member_id"] == member_id
                and charge["issue_id"] == issue_id
                and charge["waiver_eligible"]
                and charge["remaining"] > 0
            ):
                eligible_charge = charge
                break

        if eligible_charge is None:
            self.log_result(
                command, member_id, issue_id,
                timestamp, "REJECTED", "NO_OUTSTANDING_FINE"
            )
            return False

        maximum_unpaid = round(
            eligible_charge["remaining"], 2
        )

        allowed_amount = min(
            remaining_waiver_limit,
            maximum_unpaid
        )

        if amount > allowed_amount:
            self.log_result(
                command, member_id, issue_id,
                timestamp, "REJECTED", "WAIVER_LIMIT_EXCEEDED"
            )
            return False

        eligible_charge["remaining"] = round(
            eligible_charge["remaining"] - amount, 2
        )

        issue["waived"] = round(
            already_waived + amount, 2
        )

        member["outstanding"] = round(
            max(0, member["outstanding"] - amount), 2
        )

        self.ledger.append({
            "member_id": member_id,
            "entry_ts": timestamp,
            "entry_type": "WAIVER",
            "reference": issue_id,
            "amount": -amount,
            "balance_after": member["outstanding"]
        })

        self.log_result(
            command,
            member_id,
            issue_id,
            timestamp,
            "OK",
            "",
            "",
            -amount
        )

        return True

    # -------------------------------
    # COMMAND VALIDATION
    # -------------------------------

    def validate_commands(self):
        valid_operations = {
            "ISSUE",
            "RETURN",
            "RENEW",
            "HOLD",
            "INSPECT",
            "ILL_REQUEST",
            "ILL_RECEIVE",
            "ILL_RETURN",
            "PAY",
            "WAIVE",
            "PRINT_DAILY_SUMMARY",
            "PRINT_OVERDUE",
            "PRINT_STATEMENT",
            "PRINT_HOLD_QUEUE"
        }

        return [
            command for command in self.commands
            if command["parts"][0] not in valid_operations
        ]

    # -------------------------------
    # MAIN PROCESSING
    # -------------------------------

    def run(self):
        print("\nLIBRARY CIRCULATION ENGINE")
        print("--------------------------")

        print("Members loaded:", len(self.members))
        print("Titles loaded:", len(self.titles))
        print("Copies loaded:", len(self.copies))
        print("Partners loaded:", len(self.partners))
        print("Partner holdings loaded:", len(self.partner_holdings))
        print("Closed days loaded:", len(self.closed_days))
        print("Commands loaded:", len(self.commands))

        invalid = self.validate_commands()

        print("\nInvalid commands:", len(invalid))

        operations = [
            "ISSUE",
            "RETURN",
            "RENEW",
            "HOLD",
            "INSPECT",
            "ILL_REQUEST",
            "ILL_RECEIVE",
            "ILL_RETURN",
            "PAY",
            "WAIVE"
        ]

        successful = {
            operation: 0 for operation in operations
        }

        rejected = {
            operation: 0 for operation in operations
        }

        for command in self.commands:
            operation = command["parts"][0]
            event_date = self.command_event_date(command)
            if event_date is not None:
                self.process_daily_events_until(event_date)

            if operation == "ISSUE":
                result = self.issue_book(command)

            elif operation == "RETURN":
                result = self.return_book(command)

            elif operation == "RENEW":
                result = self.renew_book(command)

            elif operation == "HOLD":
                result = self.place_hold(command)

            elif operation == "INSPECT":
                result = self.inspect_book(command)

            elif operation == "ILL_REQUEST":
                result = self.ill_request(command)

            elif operation == "ILL_RECEIVE":
                result = self.ill_receive(command)

            elif operation == "ILL_RETURN":
                result = self.ill_return(command)

            elif operation == "PAY":
                result = self.pay_fine(command)

            elif operation == "WAIVE":
                result = self.waive_fine(command)

            else:
                continue

            if result:
                successful[operation] += 1
            else:
                rejected[operation] += 1

        print("\nTRANSACTION RESULTS")
        print("-------------------")

        for operation in operations:
            print(
                f"Successful {operation}:",
                successful[operation]
            )

            print(
                f"Rejected {operation}:",
                rejected[operation]
            )

        print("\nTOTALS")
        print("------")

        print("Total issue records:", len(self.issues))
        print("Total holds placed:", len(self.holds))
        print("Total ILL requests:", len(self.ill_requests))
        print("Total ledger entries:", len(self.ledger))

        print("\nHOLD STATISTICS")
        print("---------------")

        print(
            "Pending holds:",
            sum(1 for h in self.holds if h["status"] == "PENDING")
        )

        print(
            "Holds on shelf:",
            sum(
                1 for h in self.holds
                if h["status"] == "ON_HOLD_SHELF"
            )
        )

        print(
            "Collected holds:",
            sum(1 for h in self.holds if h["status"] == "COLLECTED")
        )

        print("\nILL STATISTICS")
        print("--------------")

        print(
            "Requested:",
            sum(
                1 for r in self.ill_requests.values()
                if r["status"] == "REQUESTED"
            )
        )

        print(
            "Received:",
            sum(
                1 for r in self.ill_requests.values()
                if r["status"] == "RECEIVED"
            )
        )

        print(
            "Returned:",
            sum(
                1 for r in self.ill_requests.values()
                if r["status"] == "RETURNED"
            )
        )

        print("\nPAYMENT STATISTICS")
        print("------------------")

        print("Successful payments:", successful["PAY"])
        print("Rejected payments:", rejected["PAY"])
        print("Successful waivers:", successful["WAIVE"])
        print("Rejected waivers:", rejected["WAIVE"])

        print("\nNOTE")
        print("----")
        print("LOST-book processing and daily hold expiry are enabled.")
        print("LOST books returned within 30 days receive a replacement-price refund.")


if __name__ == "__main__":
    engine = LibraryEngine()
    engine.run()