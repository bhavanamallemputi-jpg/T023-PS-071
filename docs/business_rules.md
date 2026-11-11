# Library Circulation Engine
## Business Rule Register
**Team ID:** T023  
**Problem Statement:** PS-071  
**Project:** Library Circulation Engine with Holds, Fines and Inter-Library Loans

### BR-01: Loan Limits and Loan Periods
- UG members can borrow a maximum of 3 items for 14 days.
- PG members can borrow 5 items for 21 days.
- RESEARCH members can borrow 8 items for 30 days.
- FACULTY members can borrow 10 items for 90 days.
- EXTERNAL members can borrow 2 items for 7 days.
- JOURNAL and DVD loans are always limited to 7 days.
- REFERENCE and THESIS items cannot be issued except to FACULTY members for 2 days.

### BR-02: Due Dates and Closed Days
- If the calculated due date falls on a library closed day, move it to the next open day.
- Fines do not accrue on library closed days.

### BR-03: Fine Calculation
- A one-day grace period applies to normal items.
- First 7 overdue days: Rs. 2 per day.
- After 7 overdue days: Rs. 5 per day.
- JOURNAL and DVD: Rs. 10 per day without a grace period.
- Maximum fine cannot exceed the item's price or Rs. 500, whichever is lower.

### BR-04: Member Blocking
A member is blocked if:
- Outstanding fines exceed Rs. 200.
- Any item is overdue by more than 30 days.
- Membership has expired.

A financial or overdue block is automatically lifted when the relevant conditions are cleared. Expired membership remains blocked until membership validity is restored.

### BR-05: Renewal Rules
- Maximum two renewals per issue.
- Renewal period is calculated from the renewal date.
- Renewal is allowed only when the item is not overdue and no hold exists for its title.
- Renewal within two days before the due date is allowed.
- Earlier renewal requests are rejected.

### BR-06: Hold Rules
- Holds are allowed only when all copies of a title are issued.
- Hold priority: FACULTY first, RESEARCH second, then timestamp order.
- A member can hold a maximum of three titles.
- A member cannot place a hold on a title currently borrowed by them.

### BR-07: Hold Shelf and Expiry
- When a returned copy has a pending hold, it is placed ON_HOLD_SHELF for the highest-priority member.
- The member has three open days to collect the item.
- If not collected, the hold is cancelled and the next member receives the opportunity.
- Two expired holds in one semester result in a 30-day hold suspension.

### BR-08: Recall Rules
- If a hold is placed and every copy of that title has been on loan for more than 14 days, recall the longest-held copy.
- The recalled item's new due date is the later of recall date plus 7 days or its original due date.
- Double overdue fines apply to recalled items.

### BR-09: Lost Items
- An item is automatically marked LOST after 60 days past its due date.
- Lost charge = item price + Rs. 100 processing fee + fine accrued up to day 60.
- If the item is returned within 30 days after being marked LOST, refund the item price.
- Processing fee and accrued fine are not refunded.
- Unpaid lost-item charges block the member.

### BR-10: Damaged Items
- Minor damage: charge 50% of the item's price.
- Major damage: charge 100% of the item's price plus Rs. 100.
- Damaged copies are withdrawn from circulation.
- Inspection determines whether damage is MINOR or MAJOR.

### BR-11: Inter-Library Loans (ILL)
- Select a partner library based on the shortest transit time when it lists the required ISBN.
- Member loan period = partner loan period minus twice the transit days.
- Minimum member loan period is 7 days.
- ILL charges range from Rs. 50 to Rs. 300 and are billed on issue.
- ILL items cannot be renewed or placed on hold.
- ILL overdue fine is Rs. 20 per day.

### BR-12: Payments and Waivers
- Payments are applied to the oldest outstanding charge first.
- Partial payments do not automatically remove blocks unless outstanding amounts fall to Rs. 200 or below and other blocking conditions are cleared.
- Librarian waivers can remove a maximum of 50% of the fine for an item.
- Lost-item price cannot be waived.

## Conclusion
The system must enforce all twelve business rules during circulation operations. Every accepted or rejected command must be recorded with an appropriate result and reason.