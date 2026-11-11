# Library Circulation Engine – Decision Log

**Team ID:** T023  
**Problem Statement:** PS-071  
**Project:** Library Circulation Engine with Holds, Fines and Inter-Library Loans

| ID | Decision | Reason |
|---|---|---|
| D01 | Use Python 3.10+ | Python supports quick development and testing. |
| D02 | Use an object-oriented design | To organize the system into reusable classes. |
| D03 | Use CSV files for input data | The sample dataset is provided in CSV format. |
| D04 | Use commands.txt as the command source | It contains the circulation operations to process. |
| D05 | Process commands in file order | The assignment requires strict file-order processing. |
| D06 | Preserve command order for identical timestamps | It determines which operation happens first. |
| D07 | Use separate classes for members, titles and copies | To maintain clear responsibilities. |
| D08 | Maintain individual copy status | Each physical copy has its own circulation state. |
| D09 | Use a separate Loan record | To preserve issue and return history. |
| D10 | Maintain a separate member ledger | To track charges, payments and refunds. |
| D11 | Use a priority-based hold queue | To implement FACULTY and RESEARCH priority. |
| D12 | Use the library calendar for closed days | To calculate due dates and fines correctly. |
| D13 | Apply fine limits using item price and Rs. 500 | To enforce the maximum fine rule. |
| D14 | Separate ILL transactions from normal loans | ILL has different loan and fine conditions. |
| D15 | Validate commands before changing records | To prevent invalid operations. |
| D16 | Generate the five required CSV output files | To match the assignment submission format. |
| D17 | Use pytest for automated testing | To verify business rules and edge cases. |
| D18 | Keep business logic separate from file handling | To improve maintainability and testing. |

## Pending Clarifications

1. Confirm how a returned LOST item is represented in copy and loan status.
2. Confirm how fine calculations handle a partially overdue period containing closed days.
3. Confirm how a member's multiple blocking reasons are cleared.
4. Confirm the exact meaning of a semester for hold suspension.

These questions will be resolved using the assignment specification and documented implementation decisions.

## Conclusion

The decisions above establish the initial technical design of the Library Circulation Engine. They will guide implementation, testing and future maintenance.