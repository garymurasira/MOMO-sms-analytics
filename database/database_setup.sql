-- =====================================================================
-- MoMo SMS Analytics — Database Setup
-- File: database/database_setup.sql
-- Purpose: Create schema (DDL) and seed sample data (DML)
-- Engine : MySQL 8.x
-- =====================================================================

DROP DATABASE IF EXISTS momo_sms;
CREATE DATABASE momo_sms
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE momo_sms;

-- ---------------------------------------------------------------------
-- 1) users — every person/entity that appears in a transaction
-- ---------------------------------------------------------------------
CREATE TABLE users (
  user_id        INT AUTO_INCREMENT PRIMARY KEY               COMMENT 'Surrogate PK for a user/counterparty',
  full_name      VARCHAR(100) NOT NULL                        COMMENT 'Display name as it appears in the SMS',
  phone_number   VARCHAR(20)  UNIQUE                          COMMENT 'MSISDN in international format, nullable for merchants',
  user_type      ENUM('CUSTOMER','AGENT','MERCHANT','BANK','SYSTEM') NOT NULL DEFAULT 'CUSTOMER'
                                                              COMMENT 'Classifies the actor for analytics',
  created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                                                              COMMENT 'Row insert time'
) COMMENT='All persons / entities involved in MoMo transactions';

-- ---------------------------------------------------------------------
-- 2) transaction_categories — lookup of transaction types
-- ---------------------------------------------------------------------
CREATE TABLE transaction_categories (
  category_id    INT AUTO_INCREMENT PRIMARY KEY               COMMENT 'Surrogate PK for a category',
  category_name  VARCHAR(60)  NOT NULL UNIQUE                 COMMENT 'Human readable category name',
  description    VARCHAR(255)                                 COMMENT 'Short description of the category'
) COMMENT='Lookup table for MoMo transaction categories';

-- ---------------------------------------------------------------------
-- 3) transactions — one row per parsed MoMo SMS
-- ---------------------------------------------------------------------
CREATE TABLE transactions (
  transaction_id   INT AUTO_INCREMENT PRIMARY KEY             COMMENT 'Surrogate PK',
  external_txn_id  VARCHAR(40)  UNIQUE                        COMMENT 'TxId / Financial Transaction Id from the SMS',
  category_id      INT NOT NULL                               COMMENT 'FK -> transaction_categories.category_id',
  amount           DECIMAL(12,2) NOT NULL                     COMMENT 'Principal amount in RWF',
  fee              DECIMAL(12,2) NOT NULL DEFAULT 0.00        COMMENT 'Fee charged in RWF',
  new_balance      DECIMAL(12,2)                              COMMENT 'Balance after this transaction',
  transaction_date DATETIME NOT NULL                          COMMENT 'When the transaction happened',
  raw_message      TEXT                                       COMMENT 'Original SMS body for traceability',
  created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Row insert time',
  CONSTRAINT fk_tx_category
    FOREIGN KEY (category_id) REFERENCES transaction_categories(category_id)
) COMMENT='Main MoMo transaction facts';

CREATE INDEX idx_tx_category   ON transactions(category_id);
CREATE INDEX idx_tx_date       ON transactions(transaction_date);

-- ---------------------------------------------------------------------
-- 4) transaction_participants — junction for M:N (transactions <-> users)
-- ---------------------------------------------------------------------
CREATE TABLE transaction_participants (
  participant_id  INT AUTO_INCREMENT PRIMARY KEY              COMMENT 'Surrogate PK for the link row',
  transaction_id  INT NOT NULL                                COMMENT 'FK -> transactions.transaction_id',
  user_id         INT NOT NULL                                COMMENT 'FK -> users.user_id',
  role            ENUM('SENDER','RECEIVER') NOT NULL          COMMENT 'Direction of the participation',
  CONSTRAINT fk_tp_tx
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
    ON DELETE CASCADE,
  CONSTRAINT fk_tp_user
    FOREIGN KEY (user_id) REFERENCES users(user_id),
  CONSTRAINT uq_tp_tx_user_role UNIQUE (transaction_id, user_id, role)
) COMMENT='Junction table resolving the many-to-many between transactions and users';

CREATE INDEX idx_tp_tx   ON transaction_participants(transaction_id);
CREATE INDEX idx_tp_user ON transaction_participants(user_id);

-- ---------------------------------------------------------------------
-- 5) system_logs — pipeline log entries
-- ---------------------------------------------------------------------
CREATE TABLE system_logs (
  log_id         INT AUTO_INCREMENT PRIMARY KEY               COMMENT 'Surrogate PK',
  transaction_id INT                                          COMMENT 'Optional FK -> transactions.transaction_id',
  log_level      ENUM('INFO','WARN','ERROR') NOT NULL DEFAULT 'INFO'
                                                              COMMENT 'Severity of the log entry',
  message        VARCHAR(255) NOT NULL                        COMMENT 'Short human readable message',
  created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'When this log row was created',
  CONSTRAINT fk_log_tx
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
    ON DELETE SET NULL
) COMMENT='Audit / processing trail for the ETL pipeline';

CREATE INDEX idx_log_tx ON system_logs(transaction_id);

-- =====================================================================
-- SEED DATA (DML)
-- =====================================================================

INSERT INTO users (full_name, phone_number, user_type) VALUES
('Samuel Carter',      '+250788111001', 'CUSTOMER'),
('Jane Smith',         '+250788222002', 'CUSTOMER'),
('Direct Payment Ltd',  NULL,           'MERCHANT'),
('Bank of Kigali',      NULL,           'BANK'),
('MTN Agent 54321',    '+250788333003', 'AGENT');

INSERT INTO transaction_categories (category_name, description) VALUES
('Incoming Money',          'Funds received into the MoMo wallet'),
('Payment to Code Holder',  'Payment to a registered merchant code'),
('Transfer to Mobile',      'Peer-to-peer transfer to another MoMo user'),
('Bank Deposit',            'Deposit from a linked bank account'),
('Airtime Purchase',        'Buying airtime from the wallet');

INSERT INTO transactions
  (external_txn_id, category_id, amount, fee, new_balance, transaction_date, raw_message)
VALUES
('TX1001', 1, 25000.00,   0.00, 25000.00, '2024-05-10 09:12:00', 'You have received 25000 RWF from Jane Smith.'),
('TX1002', 2,  4500.00,  50.00, 20450.00, '2024-05-10 12:30:00', 'TxId: TX1002. Your payment of 4500 RWF to Direct Payment Ltd.'),
('TX1003', 3, 10000.00, 100.00, 10350.00, '2024-05-11 08:05:00', '10000 RWF transferred to Jane Smith.'),
('TX1004', 4, 50000.00,   0.00, 60350.00, '2024-05-11 15:45:00', 'Bank deposit of 50000 RWF from Bank of Kigali.'),
('TX1005', 5,  1000.00,   0.00, 59350.00, '2024-05-12 07:20:00', 'Airtime purchase of 1000 RWF was successful.');

-- Junction rows: each transaction has one SENDER and one RECEIVER
INSERT INTO transaction_participants (transaction_id, user_id, role) VALUES
(1, 2, 'SENDER'),   (1, 1, 'RECEIVER'),    -- Jane -> Samuel
(2, 1, 'SENDER'),   (2, 3, 'RECEIVER'),    -- Samuel -> Direct Payment Ltd
(3, 1, 'SENDER'),   (3, 2, 'RECEIVER'),    -- Samuel -> Jane
(4, 4, 'SENDER'),   (4, 1, 'RECEIVER'),    -- Bank of Kigali -> Samuel
(5, 1, 'SENDER'),   (5, 5, 'RECEIVER');    -- Samuel -> MTN Agent

INSERT INTO system_logs (transaction_id, log_level, message) VALUES
(1,    'INFO',  'Parsed Incoming Money SMS successfully'),
(2,    'INFO',  'Parsed Payment to Code Holder SMS successfully'),
(3,    'WARN',  'Fee field inferred from balance delta'),
(NULL, 'ERROR', 'Unrecognized SMS template skipped'),
(5,    'INFO',  'Airtime purchase parsed successfully');