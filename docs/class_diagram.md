# Library Circulation Engine – Class Diagram

**Team ID:** T023  
**Problem Statement:** PS-071

## 1. Classes and Responsibilities

### Member
- member_id
- member_name
- category
- membership_start
- membership_expiry
- standing
- outstanding_balance

Responsibilities:
- Store member information.
- Check membership validity.
- Check borrowing eligibility.

### Title
- title_id
- title
- author
- category
- department
- publication_year

Responsibilities:
- Store library title information.
- Identify all copies belonging to a title.

### Copy
- copy_id
- title_id
- price
- acquired_date
- shelf_location
- status

Responsibilities:
- Maintain individual copy information.
- Track availability and circulation status.

### Loan
- issue_id
- member_id
- copy_or_ill_id
- issue_date
- original_due_date
- current_due_date
- renewals
- recalled
- return_date
- status
- fine

Responsibilities:
- Manage book issues.
- Process returns and renewals.
- Track overdue items.

### Hold
- hold_id
- title_id
- member_id
- placed_ts
- status
- shelf_copy_id
- shelf_expiry_date

Responsibilities:
- Manage reservations.
- Maintain hold priority.
- Handle hold expiry.

### LedgerEntry
- member_id
- entry_ts
- entry_type
- reference
- amount
- balance_after

Responsibilities:
- Record fines and charges.
- Record payments and refunds.
- Maintain member balances.

### PartnerLibrary
- partner_id
- partner_name
- city
- transit_days
- loan_period_days

Responsibilities:
- Store partner library information.
- Provide transit and loan details.

### InterLibraryLoan
- ill_id
- member_id
- isbn
- partner_id
- issue_date
- due_date
- charge
- status

Responsibilities:
- Manage external library borrowing.
- Calculate ILL loan periods.
- Track ILL returns and charges.

### LibraryCalendar
- closed_dates

Responsibilities:
- Identify library holidays.
- Calculate valid due dates.
- Exclude closed days from fine calculations.

### CirculationEngine

Responsibilities:
- Process circulation commands.
- Enforce all business rules.
- Coordinate issues, returns, renewals and holds.
- Update member records and ledger entries.

### ReportService

Responsibilities:
- Generate daily summaries.
- Generate overdue reports.
- Generate member statements.
- Generate hold queue reports.

## 2. Class Relationships

- One Member can have multiple Loans.
- One Member can have multiple Holds.
- One Member can have multiple LedgerEntries.
- One Title can have multiple Copies.
- One Title can have multiple Holds.
- One Copy can have multiple Loan records over time.
- One PartnerLibrary can support multiple InterLibraryLoans.
- CirculationEngine coordinates the library operations.
- ReportService generates reports using circulation and member information.

## 3. Design Explanation

The system follows an object-oriented design. Each class represents a specific library entity or service.

The CirculationEngine handles the main business operations, while the individual classes maintain their respective data and responsibilities.

This design supports modular development, validation, testing and future maintenance.