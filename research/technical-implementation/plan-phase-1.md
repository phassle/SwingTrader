# Epic: Aspire-first SwingTrader Phase 1 with Cosmos and Azure-ready path

## Summary

Build Phase 1 as an Azure-oriented local-first system where .NET Aspire orchestrates a Python scanner, Cosmos DB emulator, and local configuration for end-to-end signal generation with Telegram notifications. The implementation must work locally first on 2026-03-09 using Aspire dashboard + Cosmos emulator, and be shaped so the same topology can later be deployed through azd to Azure without redesigning the application layer.

This epic explicitly excludes a dashboard/web UI in Phase 1. It should, however, preserve clear contracts and data structures so a Phase 2 read-only dashboard can attach to the same Cosmos data later.

## Key Decisions

- Application logic stays in Python; C# is used only for the Aspire AppHost.
- Local Aspire execution uses `AddExecutable()` first for faster iteration.
- Containerization is still part of the epic, but as a later hardening feature before Azure deployment.
- Primary data store is Azure Cosmos DB NoSQL, using the emulator locally and a real Cosmos resource later.
- Azure deployment target stays Aspire/azd-compatible without locking the plan to a single Azure compute product yet.
- Telegram notifications are part of Phase 1 so the system is usable end-to-end from the first local milestone.
- Dashboard/UI is out of scope for this phase.

## Implementation Changes

### System shape

- Add a thin Aspire AppHost that orchestrates:
  - Cosmos DB emulator
  - Python scanner process
  - local environment/config injection
- Keep business logic isolated from orchestration so the Python app can run both under Aspire and outside it for debugging/tests.
- Use repository boundaries around Cosmos access so storage concerns do not leak into signal logic.

### Data and interfaces

- Standardize Phase 1 storage around these logical entities:
  - stocks
  - daily_prices
  - indicators
  - signals
  - scan_runs
- Define stable application-level contracts for:
  - scan run input/config
  - fetched price payload
  - calculated indicator payload
  - raw signal payload
  - ranked recommendation/notification payload
- Use deterministic IDs and explicit partition strategy consistent with the existing Cosmos research, so emulator and Azure behave the same.

### Delivery path

- First local milestone must prove:
  - Aspire starts cleanly
  - Cosmos emulator is reachable
  - Python scanner can fetch market data, compute indicators, persist documents, and send Telegram output
- Second milestone hardens for Azure:
  - add Dockerfile-based runtime for scanner
  - ensure env/config contract works identically under executable mode and container mode
  - add azd-ready app/deployment structure
- Azure-specific infra provisioning is planned, but the epic stops at a deployment-ready topology/spec unless later expanded.

## Feature Backlog for Speckit

### 1. Aspire AppHost foundation

Goal: establish the orchestration shell for local distributed development.

- Create the thin Aspire host project and wire Cosmos emulator with persistent local lifetime.
- Register the Python scanner as an executable resource with dependency on Cosmos readiness.
- Define the environment variable contract that Aspire injects into the Python app.
- Acceptance:
  - one command starts AppHost, emulator, and scanner
  - Aspire dashboard shows all resources and health
  - scanner receives Cosmos connection settings from Aspire, not hardcoded files

### 2. Python scanner bootstrap and config contract

Goal: make the scanner runnable and configuration-safe under Aspire.

- Define startup entrypoint, config loading, environment validation, and structured logging.
- Separate runtime config into market/universe, scan behavior, Cosmos settings, and Telegram settings.
- Fail fast on missing required config; do not allow silent partial startup.
- Acceptance:
  - scanner starts under Aspire with validated config
  - startup logs show resolved mode and dependencies without leaking secrets

### 3. Cosmos repository and container bootstrap

Goal: make Cosmos the real Phase 1 persistence layer from day one.

- Implement repository layer for stocks, daily_prices, indicators, signals, and scan_runs.
- Add idempotent startup/bootstrap that ensures database and required containers exist.
- Codify partition keys, deterministic IDs, and schema version fields.
- Acceptance:
  - local emulator is initialized automatically
  - re-running the scanner does not create uncontrolled duplicate documents
  - read/write paths are isolated from strategy code

### 4. Market data ingestion and quality pipeline

Goal: fetch and validate Swedish market data before any signal logic runs.

- Implement yfinance-based batch fetch with fallback, validation, cleaning, and freshness checks.
- Support OMX ticker universe and Swedish market timing assumptions from the research.
- Persist price history and ingestion metadata to Cosmos.
- Acceptance:
  - scanner can ingest a defined local universe end-to-end
  - failed tickers are logged and isolated
  - scan_runs records fetch outcomes and quality issues

### 5. Indicator engine and persisted analytics layer

Goal: compute reusable indicators once and store them cleanly.

- Add indicator calculation pipeline over persisted/fetched OHLCV data.
- Persist indicator snapshots with a stable schema matching Phase 1 strategy needs.
- Keep the indicator contract explicit so future strategies and dashboard queries do not depend on raw pandas column names.
- Acceptance:
  - indicator docs exist for processed tickers/dates
  - missing-history and invalid-data cases are handled deterministically

### 6. Signal engine, scoring, and recommendation assembly

Goal: transform stored market context into ranked trade recommendations.

- Implement initial Phase 1 strategy set, signal normalization, disqualifier filtering, and ranking.
- Keep raw signal generation separate from scored recommendations.
- Store both signal output and run summary so later analysis and dashboard work have a stable base.
- Acceptance:
  - a scan can yield zero or more recommendations
  - each recommendation contains enough context for review and notification
  - scoring/ranking is reproducible from stored data

### 7. Telegram notification delivery

Goal: make the local system useful by publishing actionable scan results.

- Format recommendations into concise Telegram messages with sane empty-result behavior.
- Send end-of-run summaries and failure notifications for critical scan failures.
- Ensure Telegram is downstream-only; notification failure must not corrupt stored scan data.
- Acceptance:
  - successful scans send a readable summary
  - empty recommendation days send an explicit no-setup message or configured silence mode
  - notification errors are logged and recorded in run metadata

### 8. Local operations, observability, and developer workflow

Goal: make local Aspire-based development reliable enough to iterate daily.

- Standardize logs, health/readiness signals, local run commands, and troubleshooting steps.
- Document emulator resource expectations, local secrets setup, and reset/reseed workflow.
- Define minimal smoke-test flow for "Aspire up -> scan -> Cosmos persisted -> Telegram sent".
- Acceptance:
  - a new contributor can run the system locally from the documented steps
  - common failure modes have explicit handling paths

### 9. Azure hardening and containerization path

Goal: prepare the same app topology for Azure deployment without redesign.

- Add Dockerfile-based runtime for the Python scanner.
- Align config/env contracts between executable mode and container mode.
- Add azd-compatible project/deployment structure and document the expected Azure resource mapping.
- Keep this feature focused on deployment readiness, not on adding new product behavior.
- Acceptance:
  - scanner can run both as Aspire executable and containerized workload
  - no app-layer code changes are required when moving from local emulator to Azure resource wiring
  - deployment inputs and secrets are clearly defined

## Dependency Order

1. Aspire AppHost foundation
2. Python scanner bootstrap and config contract
3. Cosmos repository and container bootstrap

4. Market data ingestion and quality pipeline

5. Indicator engine and persisted analytics layer
6. Signal engine, scoring, and recommendation assembly
7. Telegram notification delivery
8. Local operations, observability, and developer workflow
9. Azure hardening and containerization path

## Test Plan

- Local orchestration smoke test:
  - start Aspire
  - confirm Cosmos emulator healthy
  - confirm scanner starts with injected config
- Persistence tests:
  - container bootstrap is idempotent
  - deterministic IDs prevent duplicate logical records
  - repository read/write operations work against emulator
- Data pipeline tests:
  - valid batch fetch persists expected rows
  - missing/empty ticker data is isolated and recorded


- Indicator/signal tests:

  - notification failure does not fail persistence path

  - local topology remains Azure-mappable without changing application interfaces
## Public Interfaces and Contracts

- Aspire-to-app env contract:
  - scan run summary/result object
- Cosmos logical schema:
  - stocks, daily_prices, indicators, signals, scan_runs
  - explicit partition keys, document IDs, and schema versioning

## Assumptions and Defaults

- Swedish market scanning remains the initial universe focus.
- yfinance remains the Phase 1 price source.
- Cosmos uses the NoSQL API.
- Local development uses the Cosmos emulator through Aspire, not a live Azure account.
- Azure deployment should remain azd-friendly, but exact compute service selection can be finalized after Phase 1 local success.
- Dashboard and trade journal are intentionally deferred to later phases.
