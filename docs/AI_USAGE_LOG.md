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


## David — database_setup.sql 

**Tool used:** Claude (chat)

### What I used AI for (permitted scope only)
1. **MySQL syntax verification.** I had written the `CREATE TABLE` statements
   based on our team's agreed 5-table schema, but I wasn't sure about the exact
   MySQL 8 syntax for combining a column-level `COMMENT` with an `ENUM` and a
   `NOT NULL DEFAULT`. I asked Claude to confirm the correct ordering of
   clauses. I did **not** ask it to design the tables.
2. **Data type research.** I asked which type is preferred for storing money
   in MySQL (DECIMAL vs FLOAT vs DOUBLE) and why. Claude explained that
   `DECIMAL(12,2)` avoids floating-point rounding errors — I confirmed this
   against the MySQL 8 reference manual before using it.
3. **Index strategy sanity check.** I had decided to index every FK column and
   `transaction_date`. I asked Claude whether that was excessive; it confirmed
   the pattern was standard for read-heavy analytics workloads.

### What I did NOT use AI for
- The 5-entity schema design (decided in our team meeting).
- The decision to use a junction table for transactions ↔ users.
- The seed data values (taken from sample SMS in our XML).
- The order of `CREATE TABLE` statements (figured out from FK dependencies).

### How I verified AI output
- Ran the entire script in db-fiddle.com (MySQL 8.0) — zero errors.
- Confirmed seed rows exist with `SELECT COUNT(*) FROM <table>` for all 5 tables.

### Adjustments I made to AI suggestions
- Claude initially suggested `VARCHAR(255)` for `phone_number`; I shortened it
  to `VARCHAR(20)` because MSISDNs are at most ~15 characters.
- Claude's example used `BIGINT` for amount; I overrode that with
  `DECIMAL(12,2)` for the rounding reason above.
- Added `ON DELETE CASCADE` to `transaction_participants` and `ON DELETE SET NULL`
  to `system_logs` myself — decisions based on what makes sense for our domain
  (deleting a transaction should remove its participant links, but should not
  destroy historical log entries).