# API Documentation

**Base URL:** `http://localhost:8000`
**Authentication:** All endpoints require Basic Authentication.
Include an `Authorization: Basic <base64(username:password)>` header with every request.
**Credentials:** `admin` / `password123`

---

## Endpoints

### 1. GET /transactions

**Description:** Returns a list of all transactions.
**Auth required:** Yes

**Request:**
```bash
curl -u admin:password123 http://localhost:8000/transactions
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "type": "Incoming Money",
    "amount": 2000.0,
    "fee": 0.0,
    "sender": "Jane Smith",
    "receiver": "Self",
    "timestamp": "2024-05-10T14:30:58.724000+00:00"
  },
  ...
]
```

**Error codes:**
| Code | Meaning |
|---|---|
| 401 | Missing or invalid credentials |

---

### 2. GET /transactions/{id}

**Description:** Returns a single transaction by its ID.
**Auth required:** Yes

**Request:**
```bash
curl -u admin:password123 http://localhost:8000/transactions/1
```

**Response (200 OK):**
```json
{
  "id": 1,
  "type": "Incoming Money",
  "amount": 2000.0,
  "fee": 0.0,
  "new_balance": 2000.0,
  "sender": "Jane Smith",
  "receiver": "Self",
  "timestamp": "2024-05-10T14:30:58.724000+00:00"
}
```

**Error codes:**
| Code | Meaning |
|---|---|
| 401 | Missing or invalid credentials |
| 404 | Transaction with given ID not found |

---

### 3. POST /transactions

**Description:** Creates a new transaction and appends it to the dataset.
**Auth required:** Yes

**Request:**
```bash
curl -u admin:password123 -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "type": "Payment to Code Holder",
    "amount": 5000.0,
    "fee": 100.0,
    "sender": "Merci Ndekwe",
    "receiver": "MTN Rwanda",
    "timestamp": "2024-06-01T09:00:00+00:00"
  }'
```

**Response (201 Created):**
```json
{
  "id": 1692,
  "type": "Payment to Code Holder",
  "amount": 5000.0,
  "fee": 100.0,
  "sender": "Merci Ndekwe",
  "receiver": "MTN Rwanda",
  "timestamp": "2024-06-01T09:00:00+00:00"
}
```

**Error codes:**
| Code | Meaning |
|---|---|
| 400 | Request body missing or invalid JSON |
| 401 | Missing or invalid credentials |

---

### 4. PUT /transactions/{id}

**Description:** Partially updates an existing transaction. Only the fields provided in the request body are changed.
**Auth required:** Yes

**Request:**
```bash
curl -u admin:password123 -X PUT http://localhost:8000/transactions/1692 \
  -H "Content-Type: application/json" \
  -d '{"amount": 6000.0}'
```

**Response (200 OK):**
```json
{
  "id": 1692,
  "type": "Payment to Code Holder",
  "amount": 6000.0,
  "fee": 100.0,
  "sender": "Merci Ndekwe",
  "receiver": "MTN Rwanda",
  "timestamp": "2024-06-01T09:00:00+00:00"
}
```

**Error codes:**
| Code | Meaning |
|---|---|
| 400 | Request body missing or invalid JSON |
| 401 | Missing or invalid credentials |
| 404 | Transaction with given ID not found |

---

### 5. DELETE /transactions/{id}

**Description:** Deletes a transaction by its ID.
**Auth required:** Yes

**Request:**
```bash
curl -u admin:password123 -X DELETE http://localhost:8000/transactions/1692
```

**Response:** `204 No Content` (empty body)

**Error codes:**
| Code | Meaning |
|---|---|
| 401 | Missing or invalid credentials |
| 404 | Transaction with given ID not found |

---

## Authentication Details

All endpoints are protected with HTTP Basic Authentication.

- On success: the request proceeds and returns the expected response.
- On failure: the server returns `401 Unauthorized` with a `WWW-Authenticate: Basic realm="MoMo API"` header.

**Testing without credentials (expect 401):**
```bash
curl -i http://localhost:8000/transactions
```

**Testing with wrong credentials (expect 401):**
```bash
curl -i -u wronguser:wrongpass http://localhost:8000/transactions
```

---

## Error Response Format

All error responses return a JSON body:
```json
{
  "error": "Description of what went wrong"
}
```
