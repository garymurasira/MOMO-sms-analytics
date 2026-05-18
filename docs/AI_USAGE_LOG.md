# AI Usage Log

This document records how each team member used AI tools during the project, what was generated, and how outputs were verified and adjusted.

---

## Merci Ndekwe — JSON Data Modeling (Task 3)

**Date:** 2026-05-18
**Tool used:** Claude Code (claude.ai/code)

### What I used AI for
- Asked Claude to explain what JSON schemas are and how they relate to database tables, to deepen my understanding before writing
- Asked for clarification on the difference between SQL foreign keys and JSON nesting — specifically why an API embeds objects instead of using IDs
- Asked Claude to explain what a SQL-to-JSON mapping table should contain so I could write my README subsection accurately

### How I verified and adjusted the output
- Wrote all 5 entity schemas myself using the patterns I learned, choosing my own user names, phone numbers, and transaction values
- Cross-referenced every field against `database/database_setup.sql` to confirm names and data types matched
- Caught the `status` vs `log_level` mismatch myself by comparing my JSON to the SQL ENUM definition
- Reviewed the final file end-to-end to confirm the nesting structure made sense as an API response

### What I did myself
- Chose all real data values — user names (Kagabo Eric, Merci Ndekwe, Murokore David, Kazungu Denis, Equity Bank), phone numbers, amounts, and transaction dates
- Decided which users are senders and receivers for each transaction
- Wrote the 5 entity schemas and the complex nested transaction object
- Made all corrections to the file after understanding what was wrong

---
