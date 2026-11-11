# PS-071 – Library Circulation Engine with Holds, Fines and Inter-Library Loans — Sample Data Pack

Prepared by 10 SECONDS for Team T023.

## Files

| File | What it holds | Row count |
|---|---|---|
| `members.csv` | 250 members across UG / PG / RESEARCH / FACULTY / EXTERNAL with membership dates and opening balance | 250 data rows |
| `titles.csv` | 300 titles (BOOK, REFERENCE, JOURNAL, THESIS, DVD) | 300 data rows |
| `copies.csv` | ~800 physical copies with price | 800 data rows |
| `closed_days.csv` | 25 closed days (Sundays + holidays) between 2026-07-01 and 2026-10-31 | 25 data rows |
| `partners.csv` | 4 ILL partner libraries with transit and loan terms | 4 data rows |
| `partner_holdings.csv` | Titles listed by each partner (by ISBN) with ILL charge and replacement price | 71 data rows |
| `commands.txt` | ~2,000 circulation events over 4 months (issue, return, renew, hold, ILL, inspect, pay, waive, prints) | 1978 command lines (excluding comments) |

Row numbers quoted below are 1-based data-row numbers (the header is row 0). Line numbers for `commands.txt` are physical line numbers including comment lines.

## Column reference

Conventions: dates `YYYY-MM-DD`; timestamps `YYYY-MM-DD HH:MM:SS` (24h, IST, no timezone suffix); money in Rs as plain decimals with 2 places (no commas, no symbol); percentages as plain numbers (12.5 means 12.5%); booleans `true`/`false`; IDs uppercase with a fixed prefix. An empty cell means "not applicable" and only occurs in columns whose notes say so.

### `members.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| member_id | string | MEM-nnnn | — | primary key |
| member_name | string | — | — | — |
| gender | enum | — | M, F | — |
| category | enum | — | UG, PG, RESEARCH, FACULTY, EXTERNAL | drives loan limit / period and hold priority |
| department | string | — | CSE, ISE, ECE, EEE, ME, CIVIL, MBA, PHY, CHEM, MATH | — |
| mobile | string | 10 digits | — | — |
| membership_start | date | — | — | — |
| membership_expiry | date | — | — | member is BLOCKED from the day after this date |
| opening_balance | decimal | Rs | — | unpaid fines carried in on 2026-06-30 (treat as one charge dated 2026-06-30) |
| standing | enum | — | GOOD, BLOCKED | standing at period start; BLOCKED only because opening_balance > 200 |

### `titles.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| title_id | string | TTL-nnnn | — | holds are placed per title |
| title | string | — | — | — |
| author | string | — | — | — |
| category | enum | — | BOOK, REFERENCE, JOURNAL, THESIS, DVD | same for every copy of the title |
| department | string | — | — | — |
| publication_year | int | YYYY | — | — |

### `copies.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| copy_id | string | CPY-nnnnn | — | primary key; every copy starts AVAILABLE on 2026-07-01 |
| title_id | string | — | titles.csv | — |
| price | decimal | Rs | — | used for the fine cap, lost and damage charges |
| acquired_date | date | — | — | — |
| shelf_location | string | — | — | informational |

### `closed_days.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| closed_date | date | — | — | every date not listed is an open day (including dates after 2026-10-31) |
| day_of_week | enum | — | MON..SUN | informational |
| reason | string | — | — | — |

### `partners.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| partner_id | string | PTR-nn | — | — |
| partner_name | string | — | — | — |
| city | string | — | — | — |
| transit_days | int | days | — | one-way transit; ILL_RECEIVE lines in commands.txt already reflect it |
| loan_period_days | int | days | — | partner's loan period; member period = this - 2 x transit, minimum 7 |

### `partner_holdings.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| partner_id | string | — | partners.csv | — |
| isbn | string | 13 digits | — | ILL titles are not in titles.csv; requested by ISBN |
| title | string | — | — | — |
| ill_charge | decimal | Rs | 50.00-300.00 | billed to the member on ILL_RECEIVE |
| replacement_price | decimal | Rs | — | the item price for the ILL fine cap |

## Command file format

`commands.txt` holds one command per line in the form `COMMAND_NAME|arg1|arg2|...`. Commands must be processed strictly in file order. Lines starting with `#` are comments and blank lines are ignored. An empty argument (two pipes in a row) means "not supplied". Every command used in this pack:

| Command | Arguments (in order) | Meaning |
|---|---|---|
| `ISSUE` | `member_id|copy_id|timestamp` | Issue a copy (also used to collect a copy from the hold shelf) |
| `RETURN` | `copy_id|timestamp` | Return a copy; compute the fine; route to hold shelf if the title has a queue |
| `RENEW` | `member_id|copy_id|timestamp` | Renew a loan (max 2; only within 2 days of due; no hold on title; not overdue) |
| `HOLD` | `member_id|title_id|timestamp` | Place a hold on a title (all copies must be ISSUED); may trigger a recall |
| `INSPECT` | `copy_id|MINOR or MAJOR|timestamp` | Damage inspection after a return: MINOR 50% of price, MAJOR 100% + Rs 100, copy withdrawn |
| `ILL_REQUEST` | `ill_id|member_id|isbn|timestamp` | Request an inter-library loan; route to the holding partner with the shortest transit |
| `ILL_RECEIVE` | `ill_id|timestamp` | ILL item arrives and is issued to the requesting member; partner charge billed |
| `ILL_RETURN` | `ill_id|timestamp` | Member returns the ILL item (Rs 20/day if overdue) |
| `PAY` | `member_id|amount|timestamp` | Payment applied to the oldest charge first |
| `WAIVE` | `member_id|amount|timestamp` | Librarian waiver against the member's oldest fine (capped at 50% of that fine; never lost-item price) |
| `PRINT_DAILY_SUMMARY` | `date` | Daily circulation summary for that date |
| `PRINT_OVERDUE` | `date` | Overdue list as of end of that date |
| `PRINT_STATEMENT` | `member_id|as_of_date` | Member statement: loans, charges, payments, balance, block state |
| `PRINT_HOLD_QUEUE` | `title_id|as_of_date` | Hold queue for a title with shelf expiry |

## Planted scenarios

Every edge case in the brief, mapped to the exact record where it occurs, followed by extra traps.

- **EC-01 Due date on a Sunday followed by a Monday closed-day holiday**
  - MEM-0171 (RESEARCH, 30 days) borrows CPY-00622 on 2026-08-14; raw due date 2026-09-13 is a Sunday and Monday 2026-09-14 is the Ganesh Chaturthi closed day, so the due date is Tue 2026-09-15; the return on 2026-09-15 10:00 is on time (fine 0) — `commands.txt lines 709, 1218; copies.csv CPY-00622 (row 622); closed_days.csv 2026-09-14 (row 15)`
- **EC-02 Return on grace day 1 versus overdue day 2**
  - Two UG BOOK loans issued 2026-07-07, both due 2026-07-21: CPY-00523 (MEM-0034) returned 2026-07-22 = overdue day 1 (grace, fine Rs 0); CPY-00248 (MEM-0053) returned 2026-07-23 = overdue day 2 (fine Rs 2.00) — `commands.txt lines 68, 69, 334, 359`
- **EC-03 Fine reaching exactly Rs 500 on an item priced Rs 450**
  - ILL-0001 for MEM-0167: ISBN 9787323067855 held only by PTR-01 (21-day loan, 3-day transit -> 15-day member loan), replacement price Rs 450; received 2026-07-13, due 2026-07-28, returned 2026-08-27 = 25 open overdue days x Rs 20 = Rs 500 -> capped at Rs 450 (lower of Rs 500 and price) — `commands.txt lines 105, 157, 936; partner_holdings.csv PTR-01 (row 1)`
- **EC-04 Renewal requested exactly 2 days before the due date**
  - MEM-0168 (PG) borrows CPY-00501 on 2026-08-03, due 2026-08-24; RENEW on 2026-08-22 is exactly 2 days before due -> allowed, new due = renewal date + 21 days — `commands.txt lines 508, 848, 1172`
- **EC-05 Hold placed the instant the last copy is returned (race between return processing and hold)**
  - Title TTL-0160 has 2 copies, both issued; CPY-00370 is RETURNED at 2026-09-10 12:00:00 and MEM-0017 places a HOLD on TTL-0160 at the identical timestamp on the next line. File order decides: the return is processed first, so a copy is AVAILABLE and the HOLD must be REJECTED (not all copies issued); MEM-0017 then issues CPY-00370 directly at 12:05 — `commands.txt lines 1007, 1011, 1144, 1145, 1146`
- **EC-06 Recall making the new due date earlier than the original due date (must not happen)**
  - Title TTL-0201: both copies on FACULTY loan for more than 14 days (CPY-00473 since 2026-07-06, CPY-00474 since 2026-07-13) when MEM-0180 (RESEARCH) places a HOLD on 2026-08-03 -> longest-held CPY-00473 is RECALLED; recall + 7 days = 2026-08-10 is EARLIER than the original due date 2026-10-05, so the due date must stay 2026-10-05 (later of the two) — `commands.txt lines 50, 154, 516, 802, 829`
- **EC-07 Item returned on day 30 after being marked LOST**
  - MEM-0068 borrows CPY-00265 on 2026-07-01, due 2026-07-15; never returned so it is marked LOST on 2026-09-13 (due + 60 days) with price + Rs 100 + fine to day 60 and a BLOCK; it is returned on 2026-10-13 = day 30 after LOST -> price refunded, processing fee and fine stand; a partial PAY of Rs 150 follows — `commands.txt lines 5, 1664, 1691; copies.csv CPY-00265 (row 265)`
- **EC-08 ILL partner loan period of 10 days with 2-day transit each way (6 days, raised to 7)**
  - ILL-0002 for MEM-0178: ISBN 9786886396754 is listed by PTR-02 (transit 2, loan 10) and PTR-04 (transit 5) -> PTR-02 chosen (shortest transit); member loan = 10 - 2 - 2 = 6 days, raised to the 7-day minimum; ILL charge 50.00 billed on issue; returned on the 7th day 2026-08-27 (on time) — `commands.txt lines 764, 803, 939; partner_holdings.csv PTR-02 (row 2); partners.csv PTR-02 (row 2)`
- **Extra traps (not in the brief, but realistic):**
  - Same loan CPY-00501: a RENEW on 2026-08-21 (3 days before due) must be REJECTED_EARLY and must not consume one of the 2 renewals — `commands.txt line 828`
  - UG member MEM-0117 tries to ISSUE REFERENCE copy CPY-00386 -> REJECTED (REFERENCE issuable only to FACULTY, 2 days) — `commands.txt line 581`
  - UG member MEM-0117 issues 4 books on 2026-09-22 10:10-10:13; the 4th (CPY-00325) exceeds the UG limit of 3 and must be REJECTED — `commands.txt line 1348`
  - EXTERNAL member MEM-0236 has membership_expiry 2026-09-30: ISSUE on 2026-09-29 succeeds, ISSUE on 2026-10-01 must be REJECTED (expired -> BLOCKED regardless) — `commands.txt lines 1449, 1481; members.csv MEM-0236 (row 236)`
  - Duplicate RETURN of CPY-00443 one minute after it was already returned -> REJECTED (copy not on loan), no second fine — `commands.txt line 1480`
  - CPY-00446 returned and INSPECTed MAJOR -> 100% of price + Rs 100 charged to MEM-0148; copy withdrawn so title TTL-0189 drops from 3 to 2 copies — `commands.txt lines 893, 1108, 1110`

## What is NOT in this pack

Expected outputs are not provided for this set. Validate your engine with your own test suite against the rules in your brief (BR-01 … BR-nn). A separate hidden input set with the same schema will be used at final evaluation; outputs are compared field-for-field, so follow the column formats above exactly in your own output.

## Output format expected at evaluation

Produce these CSV files (header row, same conventions as above, rows sorted as stated). Where the brief is silent on a format detail the choice below is binding for evaluation.

### `circulation_log.csv`

One row per command line in file order (prints excluded).

Columns, in order: `line_no`, `command`, `member_id`, `copy_or_ref`, `event_ts`, `result`, `reason`, `due_date`, `charge`

### `issues.csv`

One row per issue (including ILL issues), sorted by issue_id. issue_id = ISS-nnnnn in order of issue.

Columns, in order: `issue_id`, `member_id`, `copy_or_ill_id`, `issue_date`, `original_due_date`, `current_due_date`, `renewals`, `recalled`, `return_date`, `status`, `fine`

### `holds.csv`

One row per hold placed, sorted by hold_id (HLD-nnnn in order placed).

Columns, in order: `hold_id`, `title_id`, `member_id`, `placed_ts`, `status`, `shelf_copy_id`, `shelf_expiry_date`

### `member_ledger.csv`

One row per charge, payment, waiver or refund, in event order.

Columns, in order: `member_id`, `entry_ts`, `entry_type`, `reference`, `amount`, `balance_after`

### `member_status.csv`

One row per PRINT_STATEMENT.

Columns, in order: `member_id`, `as_of_date`, `items_on_loan`, `outstanding`, `max_overdue_days`, `block_status`, `block_reasons`

Binding choices: `result` is OK or REJECTED; `reason` codes LIMIT, NOT_ISSUABLE, BLOCKED, EXPIRED, REJECTED_EARLY, HOLD_EXISTS, OVERDUE, MAX_RENEWALS, COPIES_AVAILABLE, HOLD_LIMIT, ON_LOAN_TO_MEMBER, NOT_ON_LOAN, HOLD_PRIVILEGE_SUSPENDED; `status` ISSUED, RETURNED, LOST, LOST_RETURNED, DAMAGED; `entry_type` OPENING, FINE, LOST_PRICE, PROCESSING_FEE, DAMAGE, ILL_CHARGE, PAYMENT, WAIVER, REFUND (charges positive, payments/waivers/refunds negative); `block_status` ACTIVE or BLOCKED; `block_reasons` pipe-free, semicolon-separated from FINES_OVER_200, OVERDUE_OVER_30, EXPIRED, LOST_UNPAID.
