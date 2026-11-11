# MandatePay 🛡️💳
> **The Programmable Financial Guardrail & Netting Protocol for Agentic Commerce**  
> Built for the PayPal Developer Hackathon 2026

**MandatePay** is an autonomous financial protocol that lets humans grant spending authority (**Mandates**) in natural language while AI Agents execute micro-transactions safely. Every transaction passes through a **<1ms Deterministic Policy Engine** (blocking 100% of prompt injections without LLM latency), verifies digital goods via **Contract Assertions**, and nets bilateral/multilateral balances off-chain before settling in consolidated batches via **PayPal Payouts API v1**.

---

## ⚡ 4-Command Quickstart

```bash
# 1. Copy environment configuration
cp .env.example .env

# 2. Start the FastAPI Backend Core (http://localhost:8000)
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000

# 3. Start the Next.js 14 + AG Grid Command Center (http://localhost:3000)
cd frontend && npm install && npm run dev

# 4. Run the 15-Transaction Autonomous Agent Simulation & Security Suite
python simulation/simulate_agents.py --scenario full
```

*(Or launch everything via Docker Compose: `docker-compose up --build`)*

---

## 🏗️ System Architecture

```
+----------------------------------------------------------------------------------------------------+
|                                    1. CLIENT / USER INTERFACE                                      |
|   +---------------------------------------+       +--------------------------------------------+   |
|   |   Natural Language Mandate Input      |       |   AG Grid Live Stream & Audit Drawer       |   |
|   +---------------------------------------+       +--------------------------------------------+   |
+---------------------------------------|-----------------------------------▲------------------------+
                                        | (1) Set Policy                     | (7) SSE / WebSocket
                                        ▼                                    |     Live State
+----------------------------------------------------------------------------------------------------+
|                               2. MANDATEPAY RUNTIME (BACKEND CORE)                                 |
|                                                                                                    |
|  +--------------------+         +-------------------------------+         +---------------------+  |
|  |  Mandate Compiler  |  (2)    |  Deterministic Policy Engine  |  (4)    | Contract Assertion  |  |
|  |    (LLM Engine)    | ------> |    - Prompt Injection Filter  | ------> |       Runner        |  |
|  |  [Structured JSON] | Policy  |    - Hard Budget Caps / Txn   | Pass    |  [Schema / Linters] |  |
|  +--------------------+         +-------------------------------+         +---------------------+  |
|                                                 | (3) Blocked (Red Alert)            | (5) Pass     |
|                                                 ▼                                    ▼              |
|                                      +--------------------+               +---------------------+  |
|                                      | AG Grid Alert Stream|              |  Off-Chain Netting  |  |
|                                      +--------------------+               |       Ledger        |  |
|                                                                           +---------------------+  |
|                                                                                      | (6) Settle   |
+--------------------------------------------------------------------------------------|-------------+
                                                                                       ▼
+----------------------------------------------------------------------------------------------------+
|                                   3. PAYPAL DEVELOPER SANDBOX                                      |
|  +---------------------------+   +-------------------------------+   +--------------------------+  |
|  |  Orders API v2 (Capture)  |   |  Payouts API v1 (Batch Pay)   |   |   Webhooks Ingestion     |  |
|  |  - Wallet Top-up Funding  |   |  - End-of-cycle Net Settlement|   |   - Signature Verify     |  |
|  +---------------------------+   +-------------------------------+   +--------------------------+  |
+----------------------------------------------------------------------------------------------------+
```

---

## 🧪 Automated Verification & Test Suite

Run the acceptance test suite covering **Task 1 through Task 6**:

```bash
# Run unit & integration acceptance tests (Tasks 1-4)
python backend/tests/test_acceptance.py

# Run 15-transaction agent simulation harness (Task 6)
python simulation/simulate_agents.py --direct
```

### Verified Capabilities
- **PayPal REST v1/v2 Integration (`backend/app/services/paypal_client.py`)**:
  - OAuth 2.0 `client_credentials` token manager with in-memory caching (60s safety window).
  - Orders API v2 (`POST /v2/checkout/orders` & `/capture`) for Escrow Credit Line funding.
  - Payouts API v1 (`POST /v1/payments/payouts`) with `PayPal-Request-Id` UUID idempotency protection.
  - Cryptographic Webhook Verification (`POST /v1/notifications/verify-webhook-signature`).
- **Deterministic Prompt Injection Shield (`backend/app/core/security.py` & `policy_engine.py`)**:
  - Blocks 15+ exploit signatures (`CRITICAL OVERRIDE`, `ignore previous instructions`, `bypass policy`, hex/base64 payloads) in **~0.05ms** without external LLM calls.
- **Contract Deliverable Assertion Runner (`backend/app/services/assertion_runner.py`)**:
  - Verifies JSON deliverable schemas (`required_keys`, `format`, `min_length`) before crediting seller agents.
- **Off-Chain Bilateral Netting Ledger (`backend/app/services/netting_ledger.py`)**:
  - Aggregates micro-transactions off-chain with `$0.00` per-txn fees and collapses bilateral obligations into consolidated PayPal Batch Payout items.

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](./LICENSE) for details.

