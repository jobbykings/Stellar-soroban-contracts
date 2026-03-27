#!/usr/bin/env bash

set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

usage() {
    cat <<'EOF'
Usage: ./scripts/orchestrate-soroban.sh [OPTIONS]

Deploy and initialize the local Soroban insurance stack in dependency order:
pool -> policy -> claims -> slashing -> governance, then prime the pool.

Options:
  --network NAME                 Stellar CLI network alias (default: local)
  --rpc-url URL                  Explicit RPC URL instead of a network alias
  --network-passphrase VALUE     Explicit network passphrase when using --rpc-url
  --source ACCOUNT               Stellar CLI source identity or account (default: alice)
  --admin ADDRESS                Admin address passed into initialization calls
  --governance-admin ADDRESS     Governance admin override (defaults to --admin)
  --token-id CONTRACT_ID         Token contract used by pool/governance init
  --pool-primer ADDRESS          Liquidity provider identity/address for priming
  --pool-prime-amount AMOUNT     Amount deposited into the pool after init (default: 1000000000)
  --min-provider-stake AMOUNT    Initial minimum provider stake (default: 10000000)
  --voting-period-days DAYS      Governance voting period (default: 7)
  --min-voting-pct PCT           Governance participation threshold (default: 51)
  --min-quorum-pct PCT           Governance quorum threshold (default: 33)
  --policy-wasm PATH             Explicit policy WASM artifact
  --claims-wasm PATH             Explicit claims WASM artifact
  --pool-wasm PATH               Explicit pool WASM artifact
  --governance-wasm PATH         Explicit governance WASM artifact
  --slashing-wasm PATH           Explicit slashing WASM artifact
  --skip-build                   Do not attempt contract builds before deploy
  --dry-run                      Print commands without executing them
  --output PATH                  Write orchestration manifest to this path
  --help                         Show this message

Environment overrides:
  STELLAR_BIN, POLICY_PACKAGE_DIR, CLAIMS_PACKAGE_DIR, POOL_PACKAGE_DIR,
  GOVERNANCE_PACKAGE_DIR, SLASHING_PACKAGE_DIR, POLICY_WASM, CLAIMS_WASM,
  POOL_WASM, GOVERNANCE_WASM, SLASHING_WASM, TOKEN_CONTRACT_ID.

Examples:
  ./scripts/orchestrate-soroban.sh --network local --token-id <token_contract_id>

  TOKEN_CONTRACT_ID=<token_contract_id> \
  CLAIMS_WASM=./artifacts/claims.wasm \
  GOVERNANCE_WASM=./artifacts/governance.wasm \
  ./scripts/orchestrate-soroban.sh --rpc-url http://localhost:8000 \
    --network-passphrase "Standalone Network ; February 2017"
EOF
}

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STELLAR_BIN="${STELLAR_BIN:-stellar}"
NETWORK="${NETWORK:-local}"
RPC_URL="${RPC_URL:-}"
NETWORK_PASSPHRASE="${NETWORK_PASSPHRASE:-}"
SOURCE_ACCOUNT="${SOURCE_ACCOUNT:-alice}"
ADMIN_ADDRESS="${ADMIN_ADDRESS:-$SOURCE_ACCOUNT}"
GOVERNANCE_ADMIN="${GOVERNANCE_ADMIN:-$ADMIN_ADDRESS}"
POOL_PRIMER="${POOL_PRIMER:-$SOURCE_ACCOUNT}"
POOL_PRIME_AMOUNT="${POOL_PRIME_AMOUNT:-1000000000}"
MIN_PROVIDER_STAKE="${MIN_PROVIDER_STAKE:-10000000}"
VOTING_PERIOD_DAYS="${VOTING_PERIOD_DAYS:-7}"
MIN_VOTING_PCT="${MIN_VOTING_PCT:-51}"
MIN_QUORUM_PCT="${MIN_QUORUM_PCT:-33}"
TOKEN_CONTRACT_ID="${TOKEN_CONTRACT_ID:-}"
SKIP_BUILD=false
DRY_RUN=false
OUTPUT_PATH="${OUTPUT_PATH:-$WORKSPACE_ROOT/deployments/soroban-orchestrator-local.json}"

ADMIN_EXPLICIT=false
GOVERNANCE_ADMIN_EXPLICIT=false
POOL_PRIMER_EXPLICIT=false

if [[ -n "${ADMIN_ADDRESS:-}" && "${ADMIN_ADDRESS}" != "${SOURCE_ACCOUNT}" ]]; then
    ADMIN_EXPLICIT=true
fi

if [[ -n "${GOVERNANCE_ADMIN:-}" && "${GOVERNANCE_ADMIN}" != "${ADMIN_ADDRESS}" ]]; then
    GOVERNANCE_ADMIN_EXPLICIT=true
fi

if [[ -n "${POOL_PRIMER:-}" && "${POOL_PRIMER}" != "${SOURCE_ACCOUNT}" ]]; then
    POOL_PRIMER_EXPLICIT=true
fi

declare -A PACKAGE_DIRS=(
    [policy]="${POLICY_PACKAGE_DIR:-contracts/policy}"
    [claims]="${CLAIMS_PACKAGE_DIR:-contracts/claims}"
    [pool]="${POOL_PACKAGE_DIR:-contracts/pool}"
    [governance]="${GOVERNANCE_PACKAGE_DIR:-contracts/governance}"
    [slashing]="${SLASHING_PACKAGE_DIR:-contracts/slashing}"
)

declare -A WASM_OVERRIDES=(
    [policy]="${POLICY_WASM:-}"
    [claims]="${CLAIMS_WASM:-}"
    [pool]="${POOL_WASM:-}"
    [governance]="${GOVERNANCE_WASM:-}"
    [slashing]="${SLASHING_WASM:-}"
)

declare -A FALLBACK_PACKAGE_DIRS=(
    [pool]="contracts/risk_pool"
)

declare -A CONTRACT_IDS=()
declare -A WASM_PATHS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --network)
            NETWORK="$2"
            shift 2
            ;;
        --rpc-url)
            RPC_URL="$2"
            shift 2
            ;;
        --network-passphrase)
            NETWORK_PASSPHRASE="$2"
            shift 2
            ;;
        --source)
            SOURCE_ACCOUNT="$2"
            if ! $ADMIN_EXPLICIT; then
                ADMIN_ADDRESS="$2"
            fi
            if ! $GOVERNANCE_ADMIN_EXPLICIT; then
                GOVERNANCE_ADMIN="$ADMIN_ADDRESS"
            fi
            if ! $POOL_PRIMER_EXPLICIT; then
                POOL_PRIMER="$2"
            fi
            shift 2
            ;;
        --admin)
            ADMIN_ADDRESS="$2"
            ADMIN_EXPLICIT=true
            if ! $GOVERNANCE_ADMIN_EXPLICIT; then
                GOVERNANCE_ADMIN="$2"
            fi
            shift 2
            ;;
        --governance-admin)
            GOVERNANCE_ADMIN="$2"
            GOVERNANCE_ADMIN_EXPLICIT=true
            shift 2
            ;;
        --token-id)
            TOKEN_CONTRACT_ID="$2"
            shift 2
            ;;
        --pool-primer)
            POOL_PRIMER="$2"
            POOL_PRIMER_EXPLICIT=true
            shift 2
            ;;
        --pool-prime-amount)
            POOL_PRIME_AMOUNT="$2"
            shift 2
            ;;
        --min-provider-stake)
            MIN_PROVIDER_STAKE="$2"
            shift 2
            ;;
        --voting-period-days)
            VOTING_PERIOD_DAYS="$2"
            shift 2
            ;;
        --min-voting-pct)
            MIN_VOTING_PCT="$2"
            shift 2
            ;;
        --min-quorum-pct)
            MIN_QUORUM_PCT="$2"
            shift 2
            ;;
        --policy-wasm)
            WASM_OVERRIDES[policy]="$2"
            shift 2
            ;;
        --claims-wasm)
            WASM_OVERRIDES[claims]="$2"
            shift 2
            ;;
        --pool-wasm)
            WASM_OVERRIDES[pool]="$2"
            shift 2
            ;;
        --governance-wasm)
            WASM_OVERRIDES[governance]="$2"
            shift 2
            ;;
        --slashing-wasm)
            WASM_OVERRIDES[slashing]="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --output)
            OUTPUT_PATH="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

trim() {
    local value="$1"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    printf '%s' "$value"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

require_command() {
    local cmd="$1"
    if ! command_exists "$cmd"; then
        log_error "Required command not found: $cmd"
        exit 1
    fi
}

network_args() {
    if [[ -n "$RPC_URL" ]]; then
        if [[ -z "$NETWORK_PASSPHRASE" ]]; then
            log_error "--network-passphrase is required when --rpc-url is used"
            exit 1
        fi
        printf '%s\n' "--rpc-url" "$RPC_URL" "--network-passphrase" "$NETWORK_PASSPHRASE"
    else
        printf '%s\n' "--network" "$NETWORK"
    fi
}

run_cmd() {
    if $DRY_RUN; then
        printf '[dry-run] '
        printf '%q ' "$@"
        printf '\n'
        return 0
    fi
    "$@"
}

capture_cmd() {
    if $DRY_RUN; then
        printf '[dry-run] '
        printf '%q ' "$@"
        printf '\n'
        printf 'DRY_RUN_RESULT\n'
        return 0
    fi
    "$@"
}

resolve_identity_address() {
    local value="$1"

    if $DRY_RUN; then
        printf '%s' "$value"
        return 0
    fi

    if command_exists "$STELLAR_BIN"; then
        local resolved
        resolved=$("$STELLAR_BIN" keys address "$value" 2>/dev/null || true)
        resolved="$(trim "$resolved")"
        if [[ -n "$resolved" ]]; then
            printf '%s' "$resolved"
            return 0
        fi
    fi

    printf '%s' "$value"
}

ensure_token_contract_id() {
    if [[ -z "$TOKEN_CONTRACT_ID" ]]; then
        log_error "Token contract id is required. Pass --token-id or set TOKEN_CONTRACT_ID."
        exit 1
    fi
}

resolve_package_dir() {
    local name="$1"
    local candidate="${PACKAGE_DIRS[$name]}"
    local absolute="$WORKSPACE_ROOT/$candidate"

    if [[ -d "$absolute" ]]; then
        printf '%s' "$absolute"
        return 0
    fi

    local fallback="${FALLBACK_PACKAGE_DIRS[$name]:-}"
    if [[ -n "$fallback" && -d "$WORKSPACE_ROOT/$fallback" ]]; then
        log_warning "Using fallback package directory for $name: $fallback"
        printf '%s' "$WORKSPACE_ROOT/$fallback"
        return 0
    fi

    printf '%s' ""
}

discover_wasm() {
    local package_dir="$1"
    local wasm_path=""

    while IFS= read -r candidate; do
        wasm_path="$candidate"
        break
    done < <(find "$package_dir/target" -type f -name '*.wasm' \
        \( -path '*/wasm32v1-none/release/*' -o -path '*/wasm32-unknown-unknown/release/*' \) \
        2>/dev/null | sort)

    printf '%s' "$wasm_path"
}

resolve_wasm_for() {
    local name="$1"
    local override="${WASM_OVERRIDES[$name]}"
    if [[ -n "$override" ]]; then
        if [[ ! -f "$override" ]]; then
            log_error "Configured $name WASM does not exist: $override"
            exit 1
        fi
        printf '%s' "$override"
        return 0
    fi

    local package_dir
    package_dir="$(resolve_package_dir "$name")"
    if [[ -z "$package_dir" ]]; then
        log_error "Unable to resolve a package directory for $name."
        log_error "Set ${name^^}_PACKAGE_DIR or ${name^^}_WASM to continue."
        exit 1
    fi

    if [[ ! -f "$package_dir/Cargo.toml" ]]; then
        log_error "Expected Cargo manifest missing for $name package: $package_dir/Cargo.toml"
        exit 1
    fi

    if ! $SKIP_BUILD; then
        log_info "Building $name contract from $package_dir"
        (
            cd "$package_dir"
            run_cmd "$STELLAR_BIN" contract build
        )
    fi

    local wasm_path
    wasm_path="$(discover_wasm "$package_dir")"
    if [[ -z "$wasm_path" ]]; then
        log_error "No WASM artifact discovered for $name under $package_dir/target"
        log_error "Pass --${name}-wasm or set ${name^^}_WASM if your build output lives elsewhere."
        exit 1
    fi

    printf '%s' "$wasm_path"
}

extract_contract_id() {
    local output="$1"
    local trimmed
    trimmed="$(printf '%s\n' "$output" | awk 'NF { line=$0 } END { print line }')"
    trimmed="$(trim "$trimmed")"
    printf '%s' "$trimmed"
}

deploy_contract() {
    local name="$1"
    local wasm_path="$2"
    log_info "Deploying $name contract"

    local cmd=("$STELLAR_BIN" contract deploy --wasm "$wasm_path" --source "$SOURCE_ACCOUNT")
    while IFS= read -r arg; do
        cmd+=("$arg")
    done < <(network_args)

    local output
    output="$(capture_cmd "${cmd[@]}")"
    local contract_id
    contract_id="$(extract_contract_id "$output")"

    if [[ -z "$contract_id" ]]; then
        log_error "Failed to determine deployed contract id for $name"
        printf '%s\n' "$output" >&2
        exit 1
    fi

    CONTRACT_IDS["$name"]="$contract_id"
    log_success "$name contract deployed: $contract_id"
}

invoke_contract() {
    local contract_name="$1"
    local source="$2"
    local fn="$3"
    shift 3

    local contract_id="${CONTRACT_IDS[$contract_name]}"
    local cmd=("$STELLAR_BIN" contract invoke --id "$contract_id" --source "$source")
    while IFS= read -r arg; do
        cmd+=("$arg")
    done < <(network_args)
    cmd+=(-- "$fn")
    while [[ $# -gt 0 ]]; do
        cmd+=("$1")
        shift
    done

    log_info "Invoking $contract_name.$fn"
    run_cmd "${cmd[@]}"
}

write_manifest() {
    local output_dir
    output_dir="$(dirname "$OUTPUT_PATH")"
    mkdir -p "$output_dir"

    cat >"$OUTPUT_PATH" <<EOF
{
  "network": "$(trim "$NETWORK")",
  "rpcUrl": "$(trim "$RPC_URL")",
  "networkPassphrase": "$(trim "$NETWORK_PASSPHRASE")",
  "sourceAccount": "$(trim "$SOURCE_ACCOUNT")",
  "admin": "$(trim "$ADMIN_ADDRESS")",
  "governanceAdmin": "$(trim "$GOVERNANCE_ADMIN")",
  "tokenContractId": "$(trim "$TOKEN_CONTRACT_ID")",
  "poolPrimer": "$(trim "$POOL_PRIMER")",
  "poolPrimeAmount": "$(trim "$POOL_PRIME_AMOUNT")",
  "minProviderStake": "$(trim "$MIN_PROVIDER_STAKE")",
  "governanceParameters": {
    "votingPeriodDays": "$(trim "$VOTING_PERIOD_DAYS")",
    "minVotingPct": "$(trim "$MIN_VOTING_PCT")",
    "minQuorumPct": "$(trim "$MIN_QUORUM_PCT")"
  },
  "contracts": {
    "policy": {
      "contractId": "$(trim "${CONTRACT_IDS[policy]:-}")",
      "wasm": "$(trim "${WASM_PATHS[policy]:-}")"
    },
    "claims": {
      "contractId": "$(trim "${CONTRACT_IDS[claims]:-}")",
      "wasm": "$(trim "${WASM_PATHS[claims]:-}")"
    },
    "pool": {
      "contractId": "$(trim "${CONTRACT_IDS[pool]:-}")",
      "wasm": "$(trim "${WASM_PATHS[pool]:-}")"
    },
    "governance": {
      "contractId": "$(trim "${CONTRACT_IDS[governance]:-}")",
      "wasm": "$(trim "${WASM_PATHS[governance]:-}")"
    },
    "slashing": {
      "contractId": "$(trim "${CONTRACT_IDS[slashing]:-}")",
      "wasm": "$(trim "${WASM_PATHS[slashing]:-}")"
    }
  }
}
EOF

    log_success "Wrote orchestration manifest to $OUTPUT_PATH"
}

main() {
    if ! $DRY_RUN; then
        require_command "$STELLAR_BIN"
        require_command find
    fi

    ensure_token_contract_id

    local admin_address
    local governance_admin
    local pool_primer
    admin_address="$(resolve_identity_address "$ADMIN_ADDRESS")"
    governance_admin="$(resolve_identity_address "$GOVERNANCE_ADMIN")"
    pool_primer="$(resolve_identity_address "$POOL_PRIMER")"

    ADMIN_ADDRESS="$admin_address"
    GOVERNANCE_ADMIN="$governance_admin"
    POOL_PRIMER="$pool_primer"

    log_info "Resolving contract artifacts"
    local name
    for name in pool policy claims slashing governance; do
        WASM_PATHS["$name"]="$(resolve_wasm_for "$name")"
        log_success "Resolved $name artifact: ${WASM_PATHS[$name]}"
    done

    log_info "Deploying Soroban contract stack"
    for name in pool policy claims slashing governance; do
        deploy_contract "$name" "${WASM_PATHS[$name]}"
    done

    log_info "Initializing contracts"
    invoke_contract pool "$SOURCE_ACCOUNT" initialize \
        --admin "$ADMIN_ADDRESS" \
        --xlm_token "$TOKEN_CONTRACT_ID" \
        --min_provider_stake "$MIN_PROVIDER_STAKE"

    invoke_contract policy "$SOURCE_ACCOUNT" initialize \
        --admin "$ADMIN_ADDRESS" \
        --risk_pool "${CONTRACT_IDS[pool]}"

    invoke_contract claims "$SOURCE_ACCOUNT" initialize \
        --admin "$ADMIN_ADDRESS" \
        --policy_contract "${CONTRACT_IDS[policy]}" \
        --risk_pool "${CONTRACT_IDS[pool]}"

    invoke_contract slashing "$SOURCE_ACCOUNT" initialize \
        --admin "$ADMIN_ADDRESS" \
        --governance_contract "${CONTRACT_IDS[governance]}" \
        --risk_pool_contract "${CONTRACT_IDS[pool]}"

    invoke_contract governance "$SOURCE_ACCOUNT" initialize \
        --admin "$GOVERNANCE_ADMIN" \
        --token_contract "$TOKEN_CONTRACT_ID" \
        --voting_period_days "$VOTING_PERIOD_DAYS" \
        --min_voting_percentage "$MIN_VOTING_PCT" \
        --min_quorum_percentage "$MIN_QUORUM_PCT" \
        --slashing_contract "${CONTRACT_IDS[slashing]}"

    log_info "Priming the risk pool"
    invoke_contract pool "$POOL_PRIMER" deposit_liquidity \
        --provider "$POOL_PRIMER" \
        --amount "$POOL_PRIME_AMOUNT"

    write_manifest

    log_success "Soroban orchestration complete"
}

main "$@"
