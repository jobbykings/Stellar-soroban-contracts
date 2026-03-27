# Soroban Contract Orchestrator

`scripts/orchestrate-soroban.sh` deploys and initializes the local Soroban insurance stack in one pass so developers can repeat integration setup without manually sequencing each contract.

The harness assumes the Soroban contract flow described in the repository README:

- `pool` initializes first because downstream contracts depend on its address.
- `policy` links to the pool.
- `claims` links to both policy and pool.
- `slashing` and `governance` are deployed before initialization, then wired together during init to handle their cross-reference.
- The pool receives an initial liquidity deposit after initialization so claims and integration scenarios can start with funded state.

## What It Configures

- Deploys `policy`, `claims`, `pool`, `governance`, and `slashing`
- Initializes governance defaults:
  - voting period days
  - minimum voting threshold
  - quorum threshold
- Primes the pool with an initial liquidity deposit
- Writes a deployment manifest containing resolved WASM paths and contract IDs

## Running It

```bash
cd stellar-insured-contracts
./scripts/orchestrate-soroban.sh \
  --network local \
  --token-id <token_contract_id>
```

If your local sandbox is not registered as a Stellar CLI network alias, use explicit RPC details instead:

```bash
./scripts/orchestrate-soroban.sh \
  --rpc-url http://localhost:8000 \
  --network-passphrase "Standalone Network ; February 2017" \
  --token-id <token_contract_id>
```

## Important Repo Note

This repository does not currently include all of the Soroban package directories named in the README. The harness is intentionally override-friendly so it can still be used while those packages are landing.

Use one of these patterns when a package is not at the default path:

```bash
CLAIMS_WASM=/absolute/path/to/claims.wasm \
GOVERNANCE_WASM=/absolute/path/to/governance.wasm \
SLASHING_WASM=/absolute/path/to/slashing.wasm \
./scripts/orchestrate-soroban.sh --network local --token-id <token_contract_id>
```

or

```bash
CLAIMS_PACKAGE_DIR=contracts/custom-claims \
POOL_PACKAGE_DIR=contracts/risk_pool \
./scripts/orchestrate-soroban.sh --network local --token-id <token_contract_id>
```

## Useful Flags

- `--dry-run` prints the exact deploy and invoke sequence without making changes
- `--skip-build` reuses existing WASM artifacts
- `--output <path>` writes the orchestration manifest to a custom location
- `--pool-prime-amount <amount>` adjusts the initial liquidity seed
- `--voting-period-days`, `--min-voting-pct`, `--min-quorum-pct` override governance bootstrap settings
