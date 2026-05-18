# Data Dictionary — MoMo SMS Analytics Database

**Author:** David Irihose
**Database:** `momo_sms`
**Engine:** MySQL 8.x
**Companion file:** `database/database_setup.sql`

This document describes every table and every column in the relational schema
that backs the MoMo SMS Analytics system. For each column we list the data
type, key/constraint role, nullability, default value, and a plain-language
description of what the column holds and why it was modeled this way.

---

## 1. `users`
Stores every person or entity that participates in a transaction — the wallet
owner, peer-to-peer counterparties, merchants, banks, and agents. Centralising
all actors in one table allows the same person to appear in many transactions
(supporting the many-to-many relationship resolved by `transaction_participants`).

| Column | Data Type | Key | Null | Default | Description |
|---|---|---|---|---|---|
| `user_id` | INT AUTO_INCREMENT | **PK** | NO | auto | Surrogate primary key uniquely identifying a user. |
| `full_name` | VARCHAR(100) | — | NO | — | Display name as it appears in the SMS body (e.g. "Jane Smith", "Direct Payment Ltd"). |
| `phone_number` | VARCHAR(20) | UNIQUE | YES | NULL | MSISDN in international format (`+250...`). Nullable because merchants/banks have no phone. |
| `user_type` | ENUM('CUSTOMER','AGENT','MERCHANT','BANK','SYSTEM') | — | NO | 'CUSTOMER' | Classifies the actor for analytics and authorization. |
| `created_at` | TIMESTAMP | — | NO | CURRENT_TIMESTAMP | Row-insert time used for audit purposes. |

---

## 2. `transaction_categories`
A lookup table holding the controlled vocabulary of MoMo transaction types.
Using a separate table (rather than a free-text column on `transactions`)
prevents inconsistent spellings, makes new categories trivial to add, and
allows category-level analytics.

| Column | Data Type | Key | Null | Default | Description |
|---|---|---|---|---|---|
| `category_id` | INT AUTO_INCREMENT | **PK** | NO | auto | Surrogate primary key for a category. |
| `category_name` | VARCHAR(60) | UNIQUE | NO | — | Canonical human-readable name (e.g. "Payment to Code Holder"). |
| `description` | VARCHAR(255) | — | YES | NULL | Optional longer description used in dashboards / API responses. |

---

## 3. `transactions`
The main fact table. One row corresponds to one parsed MoMo SMS. Holds the
financial values, timing, and the original SMS body for traceability.

| Column | Data Type | Key | Null | Default | Description |
|---|---|---|---|---|---|
| `transaction_id` | INT AUTO_INCREMENT | **PK** | NO | auto | Surrogate primary key. |
| `external_txn_id` | VARCHAR(40) | UNIQUE | YES | NULL | TxId / Financial Transaction Id extracted from the SMS (e.g. "TX1002"). Unique so the same SMS is never inserted twice. |
| `category_id` | INT | **FK → transaction_categories.category_id** | NO | — | Links the transaction to its category. |
| `amount` | DECIMAL(12,2) | — | NO | — | Principal amount in Rwandan Francs. `DECIMAL` is used to avoid floating-point rounding errors on money. |
| `fee` | DECIMAL(12,2) | — | NO | 0.00 | Transaction fee charged by the operator. Defaults to zero where no fee applies. |
| `new_balance` | DECIMAL(12,2) | — | YES | NULL | Wallet balance reported after the transaction; null if the SMS did not include it. |
| `transaction_date` | DATETIME | — | NO | — | The wall-clock time at which the transaction occurred (from the SMS, not from row insert). Indexed for time-range queries. |
| `raw_message` | TEXT | — | YES | NULL | Original SMS body kept verbatim for forensic / debugging purposes. |
| `created_at` | TIMESTAMP | — | NO | CURRENT_TIMESTAMP | Row-insert time. |

**Indexes:** `idx_tx_category` on `category_id`, `idx_tx_date` on `transaction_date`.

---

## 4. `transaction_participants`
The junction table that resolves the many-to-many relationship between
`transactions` and `users`. Each transaction normally has exactly two
participant rows (one SENDER and one RECEIVER), but the table is general
enough to support transactions involving more actors if the data model is
extended later (e.g. agent intermediaries).

| Column | Data Type | Key | Null | Default | Description |
|---|---|---|---|---|---|
| `participant_id` | INT AUTO_INCREMENT | **PK** | NO | auto | Surrogate primary key for the participation row. |
| `transaction_id` | INT | **FK → transactions.transaction_id** (ON DELETE CASCADE) | NO | — | The transaction in which the user participated. Cascade ensures stale links are removed if a transaction is deleted. |
| `user_id` | INT | **FK → users.user_id** | NO | — | The user participating in the transaction. |
| `role` | ENUM('SENDER','RECEIVER') | — | NO | — | Direction of the participation. Constrains the data so a participant must be exactly one of the two valid roles. |

**Composite unique key:** `uq_tp_tx_user_role (transaction_id, user_id, role)` — prevents the same user being recorded twice with the same role on the same transaction.
**Indexes:** `idx_tp_tx`, `idx_tp_user`.

---

## 5. `system_logs`
An audit / processing trail for the ETL pipeline. Stores `INFO`, `WARN`, and
`ERROR` events emitted while parsing the XML SMS dump. A log row may or may
not be linked to a transaction (parse failures produce logs with no
transaction).

| Column | Data Type | Key | Null | Default | Description |
|---|---|---|---|---|---|
| `log_id` | INT AUTO_INCREMENT | **PK** | NO | auto | Surrogate primary key. |
| `transaction_id` | INT | **FK → transactions.transaction_id** (ON DELETE SET NULL) | YES | NULL | Optional link to the transaction the log concerns. Set to NULL if the parent transaction is deleted (we preserve the historical log). |
| `log_level` | ENUM('INFO','WARN','ERROR') | — | NO | 'INFO' | Severity level of the entry. |
| `message` | VARCHAR(255) | — | NO | — | Short, human-readable description of the event. |
| `created_at` | TIMESTAMP | — | NO | CURRENT_TIMESTAMP | When the log was written. |

**Index:** `idx_log_tx` on `transaction_id`.

---

## Relationship Summary

| Relationship | Cardinality | Mechanism |
|---|---|---|
| `transaction_categories` → `transactions` | 1 : M | `transactions.category_id` FK |
| `transactions` ↔ `users` | M : N | Junction table `transaction_participants` |
| `transactions` → `system_logs` | 1 : M | `system_logs.transaction_id` FK (nullable) |

## Design Notes

- **Money columns** use `DECIMAL(12,2)` rather than `FLOAT` / `DOUBLE` to eliminate floating-point rounding error on currency.
- **ENUM** is used for `user_type`, `role`, and `log_level` to enforce a small, controlled set of valid values at the database level.
- **Indexes** are placed on every foreign key column plus `transactions.transaction_date` because the workload is analytical and joins/date-range filters dominate.
- **ON DELETE behaviour** is chosen per-relationship: cascade for participant links (they are meaningless without a transaction), set-null for logs (we never want to lose audit history).
- **Surrogate integer PKs** were preferred over natural keys (e.g. phone number) because natural keys can change and are often NULL for non-customer actors.

---

*End of data dictionary.*