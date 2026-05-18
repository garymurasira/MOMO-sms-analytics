USE momo_sms;

-- CHECK CONSTRAINTS

ALTER TABLE transactions
  ADD CONSTRAINT chk_amount_non_negative
    CHECK (amount >= 0);

ALTER TABLE transactions
  ADD CONSTRAINT chk_fee_non_negative
    CHECK (fee >= 0);

ALTER TABLE transactions
  ADD CONSTRAINT chk_balance_non_negative
    CHECK (new_balance >= 0);

ALTER TABLE transactions
  ADD CONSTRAINT chk_fee_not_exceed_amount
    CHECK (fee <= amount);
