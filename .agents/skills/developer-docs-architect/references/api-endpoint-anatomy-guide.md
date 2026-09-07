# API Endpoint Anatomy & Error Catalog Standard

Every Track B API reference page must implement the mandatory 6-section anatomy in exact sequence. This guarantees predictability for human developers and high-precision parsing for autonomous AI coding agents.

---

## The 6 Mandatory Anatomy Sections

### 1. Endpoint & HTTP Method
- Specify the full URI path and standard HTTP verb (`GET`, `POST`, `PUT`, `DELETE`, `PATCH`).
- Include brief purpose statement and idempotency guarantees.

### 2. Authentication & Headers
- State exact security requirements (e.g., `Bearer <JWT_TOKEN>` or `X-API-Key: <KEY>`).
- Declare required headers:
  - `Content-Type: application/json`
  - `Accept: application/json`
  - `Idempotency-Key: <UUIDv4>` (for mutating endpoints)

### 3. Request Parameters Table
Table specifying every Path, Query, and Header variable:

| Parameter | In | Type | Required | Validation Constraints | Description |
|---|---|---|---|---|---|
| `customer_id` | Path | String | Yes | UUIDv4 format | Unique customer identifier |
| `limit` | Query | Integer | No | Min: 1, Max: 100, Default: 20 | Page size limit |
| `starting_after` | Query | String | No | Cursor string | Pagination token |

### 4. Request Body Example
- Concrete, copy-pasteable JSON payload with realistic data.
- Never use empty `{}` or placeholder `'string'` values.

### 5. Response Payloads
- Provide complete responses for all standard success outcomes (`200 OK`, `201 Created`, `204 No Content`).
- Document payload schema definitions with field types and nullable attributes.

### 6. Actionable Error Catalog
Never dump raw HTTP status codes without explicit remediation instructions. Every error must specify:

| HTTP Status | Error Code | Root Cause Trigger | Concrete Developer Remediation |
|---|---|---|---|
| `400 Bad Request` | `ERR_INVALID_PAYLOAD` | Missing required field `amount` | Supply positive integer amount in cents |
| `401 Unauthorized` | `ERR_TOKEN_EXPIRED` | Expired Bearer token | Call `/v1/auth/refresh` with valid refresh token |
| `403 Forbidden` | `ERR_INSUFFICIENT_SCOPE` | Key lacks `write:charges` | Re-issue API key with required charge permissions |
| `404 Not Found` | `ERR_CUSTOMER_NOT_FOUND` | Customer ID does not exist | Verify ID against `/v1/customers` list |
| `422 Unprocessable` | `ERR_CURRENCY_MISMATCH` | Currency not supported | Use valid ISO-4217 code (`USD`, `EUR`, `GBP`) |
| `429 Too Many Requests` | `ERR_RATE_LIMIT_EXCEEDED` | Exceeded 100 req/sec quota | Back off using exponential jitter (`Retry-After`) |
| `500 Server Error` | `ERR_UPSTREAM_TIMEOUT` | Downstream bank unavailable | Retry with identical `Idempotency-Key` |
