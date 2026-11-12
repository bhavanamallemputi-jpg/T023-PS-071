\# T023 – PS-071 Decision Log



\## Project

Library Circulation Engine with Holds, Fines and Inter-Library Loans



\## Team

\- Team ID: T023

\- Members: Mallemputi Bhavana and Md Umar Abdullah

\- Section: CSDS A



\## Technical Decisions



\### 1. Programming Language

\*\*Decision:\*\* Python 3.10+



\*\*Reason:\*\* Python is easy to maintain, supports modular development, and provides useful libraries for CSV processing and automated testing.



\### 2. Data Storage

\*\*Decision:\*\* CSV files.



\*\*Reason:\*\* CSV files provide a simple way to store and exchange library records, circulation transactions, and reports.



\### 3. Project Structure

\*\*Decision:\*\* Separate source code, tests, data, documentation, and output into different folders.



\*\*Reason:\*\* This makes the project easier to understand, test, and maintain.



\### 4. Circulation Rules

\*\*Decision:\*\* Implement separate rules for member categories and item types.



\*\*Reason:\*\* Different members have different borrowing limits and loan periods. Certain materials also have special circulation restrictions.



\### 5. Fine Calculation

\*\*Decision:\*\* Calculate overdue fines according to item type, grace period, chargeable days, and maximum fine limits.



\*\*Reason:\*\* This ensures consistent fine calculation and supports the specified library policies.



\### 6. Hold Management

\*\*Decision:\*\* Use member priority and request timestamp to manage hold queues.



\*\*Reason:\*\* This provides an organized process for allocating returned books to waiting members.



\### 7. Lost Book Processing

\*\*Decision:\*\* Include replacement charges, processing fees, overdue fines, and replacement-fee refunds when eligible.



\*\*Reason:\*\* This handles books reported lost and subsequently returned.



\### 8. Inter-Library Loans

\*\*Decision:\*\* Select a suitable partner based on availability and transit time.



\*\*Reason:\*\* This supports borrowing books from partner libraries when local copies are unavailable.



\### 9. Automated Testing

\*\*Decision:\*\* Use pytest.



\*\*Reason:\*\* Automated tests help verify important circulation and hold-management scenarios.



\### 10. Version Control

\*\*Decision:\*\* Use Git and GitHub.



\*\*Reason:\*\* Version control helps track project changes and maintain a shared repository.



\## Testing Results



\- Total automated tests passed: 20

\- Failed tests: 0

\- Test framework: pytest

\- Generated CSV reports successfully.



\## Current Status



The implementation has been committed and pushed to the GitHub repository.



Repository:

https://github.com/bhavanamallemputi-jpg/T023-PS-071

