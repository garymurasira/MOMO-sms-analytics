# Database Design Rationale

## Why transactions ↔ users Is Many-to-Many

A single MoMo transaction always involves at least two parties: the person sending money and the person receiving it. If we placed `sender_id` and `receiver_id` directly on the `transactions` table, the schema would silently assume every transaction has exactly one sender and one receiver and nothing else. Real MoMo flows break that assumption — a bank deposit involves an institutional sender with no phone number, airtime purchases involve a system-side receiver, and future transaction types might add agents or intermediaries. The `transaction_participants` junction table resolves the many-to-many relationship cleanly: each row names one participant, their role (`SENDER` or `RECEIVER`), and the transaction they belong to. A composite unique constraint on `(transaction_id, user_id, role)` prevents duplicate participation rows while still allowing flexible cardinality. This design is more expressive and easier to extend than hard-coded sender/receiver columns.

## Why transaction_categories Is a Separate Lookup Table

Storing the category as a free-text `VARCHAR` on `transactions` would allow values like `"Incoming Money"`, `"incoming money"`, and `"IncomingMoney"` to coexist, corrupting aggregate queries. A normalised lookup table enforces a controlled vocabulary: every category name is unique, consistently spelled, and carries a human-readable description. Adding a new category requires a single INSERT rather than a schema change, and foreign-key enforcement guarantees no transaction can reference a non-existent category.

## Data Type Choices

`DECIMAL(12,2)` is used for `amount`, `fee`, and `new_balance` because decimal arithmetic is exact, eliminating the rounding errors that plague `FLOAT` and `DOUBLE` in financial calculations. `DATETIME` stores `transaction_date` with full timestamp precision, which matters for ordering events within the same day. `ENUM` columns (`user_type`, `role`, `log_level`) restrict values to a predefined set at the database level, making invalid states impossible to insert.

## Why phone_number Is Nullable

MTN MoMo SMS messages sometimes mask the counterparty's number — merchants and banks appear without an MSISDN. Making `phone_number` nullable correctly models this reality; a `NOT NULL` constraint would force fabricated placeholder values that corrupt analytics.

## Data Integrity and Scalability

Foreign keys on `category_id`, `transaction_id`, and `user_id` enforce referential integrity across all joins. Cascade rules (`ON DELETE CASCADE` on participant rows, `ON DELETE SET NULL` on log rows) keep orphaned data out of the database automatically. Indexes on `transaction_date`, `category_id`, `transaction_id`, and `user_id` ensure that common analytical queries — filtering by date range, grouping by category, joining participants — remain performant as the dataset grows into the millions of rows typical of a full SMS archive.
