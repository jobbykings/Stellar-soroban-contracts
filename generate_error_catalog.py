#!/usr/bin/env python3
"""
Unified Error Code Catalog Generator for Stellar Soroban Contracts

This script generates a unified error code catalog across all contracts
to ensure consistency and improve developer experience.

Usage:
    python generate_error_catalog.py --contracts-dir contracts --output error_codes.json
    python generate_error_catalog.py --validate-only --catalog error_codes.json
"""

import json
import argparse
import re
import os
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ErrorCategory(Enum):
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    STATE = "state"
    ARITHMETIC = "arithmetic"
    STORAGE = "storage"
    BUSINESS_LOGIC = "business_logic"
    CHECKPOINTING = "checkpointing"
    EMERGENCY = "emergency"
    CROSS_CONTRACT = "cross_contract"
    GOVERNANCE = "governance"
    CLAIMS = "claims"
    POLICY = "policy"
    RISK_POOL = "risk_pool"
    SLASHING = "slashing"
    ORACLE = "oracle"
    ASSET_REGISTRY = "asset_registry"
    AUDIT_TRAIL = "audit_trail"
    ALERTING = "alerting"
    MONITORING = "monitoring"

@dataclass
class ErrorCode:
    name: str
    code: int
    category: ErrorCategory
    description: str
    contract: str
    severity: str  # "critical", "high", "medium", "low"
    recovery_action: Optional[str] = None

@dataclass
class ErrorRange:
    category: ErrorCategory
    start_code: int
    end_code: int
    description: str

class UnifiedErrorCatalog:
    def __init__(self):
        self.error_codes: Dict[str, ErrorCode] = {}
        self.error_ranges: List[ErrorRange] = []
        self.contracts: Set[str] = set()
        self._initialize_error_ranges()
    
    def _initialize_error_ranges(self):
        """Initialize standardized error code ranges for each category"""
        self.error_ranges = [
            ErrorRange(ErrorCategory.AUTHORIZATION, 1, 99, "Authorization and access control errors"),
            ErrorRange(ErrorCategory.VALIDATION, 100, 199, "Input validation and parameter errors"),
            ErrorRange(ErrorCategory.STATE, 200, 299, "Contract state and invariant errors"),
            ErrorRange(ErrorCategory.ARITHMETIC, 300, 399, "Arithmetic and overflow/underflow errors"),
            ErrorRange(ErrorCategory.STORAGE, 400, 499, "Storage and data persistence errors"),
            ErrorRange(ErrorCategory.BUSINESS_LOGIC, 500, 599, "Business logic and workflow errors"),
            ErrorRange(ErrorCategory.CHECKPOINTING, 600, 699, "Checkpointing and rollback detection errors"),
            ErrorRange(ErrorCategory.EMERGENCY, 700, 799, "Emergency and pause-related errors"),
            ErrorRange(ErrorCategory.CROSS_CONTRACT, 800, 899, "Cross-contract communication errors"),
            ErrorRange(ErrorCategory.GOVERNANCE, 900, 999, "Governance and voting errors"),
            ErrorRange(ErrorCategory.CLAIMS, 1000, 1099, "Claims processing errors"),
            ErrorRange(ErrorCategory.POLICY, 1100, 1199, "Policy management errors"),
            ErrorRange(ErrorCategory.RISK_POOL, 1200, 1299, "Risk pool and liquidity errors"),
            ErrorRange(ErrorCategory.SLASHING, 1300, 1399, "Slashing and penalty errors"),
            ErrorRange(ErrorCategory.ORACLE, 1400, 1499, "Oracle and price feed errors"),
            ErrorRange(ErrorCategory.ASSET_REGISTRY, 1500, 1599, "Asset registry errors"),
            ErrorRange(ErrorCategory.AUDIT_TRAIL, 1600, 1699, "Audit trail and logging errors"),
            ErrorRange(ErrorCategory.ALERTING, 1700, 1799, "Alerting system errors"),
            ErrorRange(ErrorCategory.MONITORING, 1800, 1899, "Performance monitoring errors"),
        ]
    
    def extract_errors_from_contract(self, contract_path: str, contract_name: str) -> List[ErrorCode]:
        """Extract error definitions from a Rust contract file"""
        errors = []
        
        try:
            with open(contract_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {contract_path}: {e}")
            return errors
        
        # Find error enum definitions
        error_enum_pattern = r'#\[contracterror\][\s\S]*?pub enum (\w+) \{([\s\S]*?)\}'
        enum_matches = re.finditer(error_enum_pattern, content)
        
        for match in enum_matches:
            enum_name = match.group(1)
            enum_body = match.group(2)
            
            # Extract individual error variants
            error_pattern = r'(\w+)\s*=\s*(\d+),?\s*(?:///\s*([^\n]*))?'
            error_matches = re.finditer(error_pattern, enum_body)
            
            for error_match in error_matches:
                error_name = error_match.group(1)
                error_code = int(error_match.group(2))
                description = error_match.group(3) or ""
                
                # Determine category based on error name and code
                category = self._categorize_error(error_name, error_code)
                severity = self._determine_severity(error_name, category)
                recovery_action = self._suggest_recovery_action(error_name, category)
                
                error = ErrorCode(
                    name=error_name,
                    code=error_code,
                    category=category,
                    description=description.strip(),
                    contract=contract_name,
                    severity=severity,
                    recovery_action=recovery_action
                )
                
                errors.append(error)
                self.error_codes[f"{contract_name}.{error_name}"] = error
                self.contracts.add(contract_name)
        
        return errors
    
    def _categorize_error(self, error_name: str, error_code: int) -> ErrorCategory:
        """Categorize an error based on name and code"""
        error_lower = error_name.lower()
        
        # Authorization errors
        if any(keyword in error_lower for keyword in ['unauthorized', 'auth', 'role', 'permission', 'access']):
            return ErrorCategory.AUTHORIZATION
        
        # Validation errors
        if any(keyword in error_lower for keyword in ['invalid', 'validation', 'input', 'format', 'malformed']):
            return ErrorCategory.VALIDATION
        
        # State errors
        if any(keyword in error_lower for keyword in ['state', 'notfound', 'already', 'exists', 'initialized']):
            return ErrorCategory.STATE
        
        # Arithmetic errors
        if any(keyword in error_lower for keyword in ['overflow', 'underflow', 'arithmetic', 'divide']):
            return ErrorCategory.ARITHMETIC
        
        # Storage errors
        if any(keyword in error_lower for keyword in ['storage', 'persistent', 'temporary', 'data']):
            return ErrorCategory.STORAGE
        
        # Checkpointing errors
        if any(keyword in error_lower for keyword in ['checkpoint', 'rollback', 'corrupted', 'double']):
            return ErrorCategory.CHECKPOINTING
        
        # Emergency errors
        if any(keyword in error_lower for keyword in ['emergency', 'paused', 'halted', 'critical']):
            return ErrorCategory.EMERGENCY
        
        # Cross-contract errors
        if any(keyword in error_lower for keyword in ['contract', 'invoke', 'call', 'trusted']):
            return ErrorCategory.CROSS_CONTRACT
        
        # Governance errors
        if any(keyword in error_lower for keyword in ['governance', 'vote', 'proposal', 'quorum']):
            return ErrorCategory.GOVERNANCE
        
        # Claims errors
        if any(keyword in error_lower for keyword in ['claim', 'payout', 'evidence', 'settlement']):
            return ErrorCategory.CLAIMS
        
        # Policy errors
        if any(keyword in error_lower for keyword in ['policy', 'premium', 'coverage', 'expiry']):
            return ErrorCategory.POLICY
        
        # Risk pool errors
        if any(keyword in error_lower for keyword in ['pool', 'liquidity', 'reserve', 'provider', 'insufficient']):
            return ErrorCategory.RISK_POOL
        
        # Slashing errors
        if any(keyword in error_lower for keyword in ['slash', 'penalty', 'forfeit', 'stake']):
            return ErrorCategory.SLASHING
        
        # Oracle errors
        if any(keyword in error_lower for keyword in ['oracle', 'price', 'feed', 'signature']):
            return ErrorCategory.ORACLE
        
        # Asset registry errors
        if any(keyword in error_lower for keyword in ['asset', 'token', 'registry', 'mint']):
            return ErrorCategory.ASSET_REGISTRY
        
        # Audit trail errors
        if any(keyword in error_lower for keyword in ['audit', 'trail', 'log', 'record']):
            return ErrorCategory.AUDIT_TRAIL
        
        # Alerting errors
        if any(keyword in error_lower for keyword in ['alert', 'notification', 'trigger']):
            return ErrorCategory.ALERTING
        
        # Monitoring errors
        if any(keyword in error_lower for keyword in ['monitor', 'performance', 'metric']):
            return ErrorCategory.MONITORING
        
        # Default to business logic
        return ErrorCategory.BUSINESS_LOGIC
    
    def _determine_severity(self, error_name: str, category: ErrorCategory) -> str:
        """Determine error severity based on name and category"""
        error_lower = error_name.lower()
        
        # Critical severity
        if any(keyword in error_lower for keyword in ['critical', 'emergency', 'security', 'rollback']):
            return "critical"
        
        # High severity
        if category in [ErrorCategory.AUTHORIZATION, ErrorCategory.EMERGENCY, ErrorCategory.CHECKPOINTING]:
            return "high"
        
        if any(keyword in error_lower for keyword in ['overflow', 'corrupted', 'unauthorized']):
            return "high"
        
        # Medium severity
        if category in [ErrorCategory.STATE, ErrorCategory.BUSINESS_LOGIC, ErrorCategory.GOVERNANCE]:
            return "medium"
        
        # Low severity
        if category in [ErrorCategory.VALIDATION, ErrorCategory.MONITORING]:
            return "low"
        
        return "medium"
    
    def _suggest_recovery_action(self, error_name: str, category: ErrorCategory) -> Optional[str]:
        """Suggest recovery action for an error"""
        error_lower = error_name.lower()
        
        if 'unauthorized' in error_lower:
            return "Check permissions and ensure proper role assignment"
        
        if 'invalid' in error_lower:
            return "Validate input parameters and retry with correct values"
        
        if 'notfound' in error_lower:
            return "Ensure the resource exists before attempting to access it"
        
        if 'already' in error_lower:
            return "Check if the operation was already completed"
        
        if 'overflow' in error_lower:
            return "Use smaller values or implement proper bounds checking"
        
        if 'paused' in error_lower:
            return "Wait for contract to be unpaused or contact admin"
        
        if 'insufficient' in error_lower:
            return "Add more funds/liquidity or reduce operation amount"
        
        if category == ErrorCategory.CHECKPOINTING:
            return "Verify system state and contact administrators if needed"
        
        return "Review error details and consult documentation"
    
    def scan_contracts_directory(self, contracts_dir: str) -> None:
        """Scan all contracts in the directory for error definitions"""
        contracts_path = Path(contracts_dir)
        
        if not contracts_path.exists():
            print(f"Contracts directory {contracts_dir} not found")
            return
        
        # Find all Rust files that contain contracterror
        rust_files = []
        for rust_file in contracts_path.rglob("*.rs"):
            try:
                with open(rust_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'contracterror' in content:
                        rust_files.append(rust_file)
            except Exception as e:
                print(f"Error reading {rust_file}: {e}")
        
        print(f"Found {len(rust_files)} Rust files with contracterror definitions")
        
        # Process each file
        for rust_file in rust_files:
            # Determine contract name from directory structure
            if rust_file.name == 'lib.rs':
                contract_name = rust_file.parent.name
            else:
                contract_name = rust_file.parent.parent.name
            
            print(f"Scanning contract: {contract_name} ({rust_file})")
            errors = self.extract_errors_from_contract(str(rust_file), contract_name)
            print(f"  Found {len(errors)} error definitions")
    
    def validate_error_codes(self) -> List[str]:
        """Validate error codes for conflicts and consistency"""
        issues = []
        
        # Check for duplicate error codes
        code_usage: Dict[int, List[str]] = {}
        for key, error in self.error_codes.items():
            if error.code not in code_usage:
                code_usage[error.code] = []
            code_usage[error.code].append(key)
        
        for code, keys in code_usage.items():
            if len(keys) > 1:
                issues.append(f"Duplicate error code {code} used by: {', '.join(keys)}")
        
        # Check for out-of-range error codes
        for key, error in self.error_codes.items():
            range_found = False
            for error_range in self.error_ranges:
                if error_range.start_code <= error.code <= error_range.end_code:
                    range_found = True
                    break
            
            if not range_found:
                issues.append(f"Error code {error.code} in {key} is outside defined ranges")
        
        # Check for inconsistent naming
        for key, error in self.error_codes.items():
            if not error.name.isupper() or '_' not in error.name:
                issues.append(f"Inconsistent error naming: {key} (should be UPPER_SNAKE_CASE)")
        
        return issues
    
    def generate_catalog(self) -> Dict:
        """Generate the complete error catalog"""
        catalog = {
            "version": "1.0.0",
            "generated_at": "2026-03-25T12:28:00Z",
            "contracts": list(self.contracts),
            "error_ranges": [
                {
                    "category": range.category.value,
                    "start_code": range.start_code,
                    "end_code": range.end_code,
                    "description": range.description
                }
                for range in self.error_ranges
            ],
            "errors": {}
        }
        
        # Group errors by category
        for category in ErrorCategory:
            catalog["errors"][category.value] = {}
        
        # Add errors to catalog
        for key, error in self.error_codes.items():
            catalog["errors"][error.category.value][key] = {
                "name": error.name,
                "code": error.code,
                "description": error.description,
                "contract": error.contract,
                "severity": error.severity,
                "recovery_action": error.recovery_action
            }
        
        return catalog
    
    def generate_rust_module(self) -> str:
        """Generate Rust module code for unified error handling"""
        rust_code = '''//! Unified Error Code Catalog for Stellar Soroban Contracts
//!
//! This module provides standardized error codes across all contracts
//! to ensure consistency and improve developer experience.

use soroban_sdk::contracterror;

/// Unified error categories with their code ranges
pub mod error_ranges {
    pub const AUTHORIZATION_START: u32 = 1;
    pub const AUTHORIZATION_END: u32 = 99;
    pub const VALIDATION_START: u32 = 100;
    pub const VALIDATION_END: u32 = 199;
    pub const STATE_START: u32 = 200;
    pub const STATE_END: u32 = 299;
    pub const ARITHMETIC_START: u32 = 300;
    pub const ARITHMETIC_END: u32 = 399;
    pub const STORAGE_START: u32 = 400;
    pub const STORAGE_END: u32 = 499;
    pub const BUSINESS_LOGIC_START: u32 = 500;
    pub const BUSINESS_LOGIC_END: u32 = 599;
    pub const CHECKPOINTING_START: u32 = 600;
    pub const CHECKPOINTING_END: u32 = 699;
    pub const EMERGENCY_START: u32 = 700;
    pub const EMERGENCY_END: u32 = 799;
    pub const CROSS_CONTRACT_START: u32 = 800;
    pub const CROSS_CONTRACT_END: u32 = 899;
    pub const GOVERNANCE_START: u32 = 900;
    pub const GOVERNANCE_END: u32 = 999;
    pub const CLAIMS_START: u32 = 1000;
    pub const CLAIMS_END: u32 = 1099;
    pub const POLICY_START: u32 = 1100;
    pub const POLICY_END: u32 = 1199;
    pub const RISK_POOL_START: u32 = 1200;
    pub const RISK_POOL_END: u32 = 1299;
    pub const SLASHING_START: u32 = 1300;
    pub const SLASHING_END: u32 = 1399;
    pub const ORACLE_START: u32 = 1400;
    pub const ORACLE_END: u32 = 1499;
    pub const ASSET_REGISTRY_START: u32 = 1500;
    pub const ASSET_REGISTRY_END: u32 = 1599;
    pub const AUDIT_TRAIL_START: u32 = 1600;
    pub const AUDIT_TRAIL_END: u32 = 1699;
    pub const ALERTING_START: u32 = 1700;
    pub const ALERTING_END: u32 = 1799;
    pub const MONITORING_START: u32 = 1800;
    pub const MONITORING_END: u32 = 1899;
}

/// Unified contract error enum with all standard error codes
#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
pub enum UnifiedError {
    // Authorization errors (1-99)
    Unauthorized = 1,
    InvalidRole = 2,
    RoleNotFound = 3,
    NotTrustedContract = 4,
    InsufficientPermissions = 5,
    AccessDenied = 6,
    
    // Validation errors (100-199)
    InvalidInput = 100,
    InvalidAmount = 101,
    InvalidAddress = 102,
    InvalidSignature = 103,
    InvalidTimestamp = 104,
    InvalidFormat = 105,
    MissingRequiredField = 106,
    OutOfBounds = 107,
    
    // State errors (200-299)
    NotInitialized = 200,
    AlreadyInitialized = 201,
    NotFound = 202,
    AlreadyExists = 203,
    InvalidState = 204,
    StateTransition = 205,
    
    // Arithmetic errors (300-399)
    Overflow = 300,
    Underflow = 301,
    DivisionByZero = 302,
    InvalidCalculation = 303,
    
    // Storage errors (400-499)
    StorageError = 400,
    DataCorrupted = 401,
    InsufficientStorage = 402,
    
    // Business logic errors (500-599)
    BusinessLogicError = 500,
    WorkflowError = 501,
    ConditionNotMet = 502,
    
    // Checkpointing errors (600-699)
    CheckpointNotFound = 600,
    RollbackDetected = 601,
    DoubleApplication = 602,
    CheckpointCorrupted = 603,
    
    // Emergency errors (700-799)
    EmergencyMode = 700,
    Paused = 701,
    Halted = 702,
    CriticalError = 703,
    
    // Cross-contract errors (800-899)
    ContractCallFailed = 800,
    InvalidContract = 801,
    ContractNotResponding = 802,
    
    // Governance errors (900-999)
    ProposalNotFound = 900,
    VotingPeriodEnded = 901,
    QuorumNotMet = 902,
    AlreadyVoted = 903,
    
    // Claims errors (1000-1099)
    ClaimNotFound = 1000,
    ClaimAlreadyProcessed = 1001,
    EvidenceInvalid = 1002,
    ClaimExpired = 1003,
    
    // Policy errors (1100-1199)
    PolicyNotFound = 1100,
    PolicyExpired = 1101,
    CoverageInsufficient = 1102,
    PremiumNotPaid = 1103,
    
    // Risk pool errors (1200-1299)
    InsufficientLiquidity = 1200,
    ProviderNotFound = 1201,
    InsufficientStake = 1202,
    LiquidityViolation = 1203,
    
    // Slashing errors (1300-1399)
    SlashConditionNotMet = 1300,
    SlashingFailed = 1301,
    StakeInsufficient = 1302,
    
    // Oracle errors (1400-1499)
    OracleUnavailable = 1400,
    InvalidPriceData = 1401,
    OracleSignatureInvalid = 1402,
    PriceStale = 1403,
    
    // Asset registry errors (1500-1599)
    AssetNotFound = 1500,
    AssetAlreadyRegistered = 1501,
    InvalidAsset = 1502,
    
    // Audit trail errors (1600-1699)
    AuditLogFailed = 1600,
    AuditRecordCorrupted = 1601,
    
    // Alerting errors (1700-1799)
    AlertFailed = 1700,
    AlertConfigInvalid = 1701,
    
    // Monitoring errors (1800-1899)
    MonitoringError = 1800,
    MetricCollectionFailed = 1801,
}

impl UnifiedError {
    /// Get the error category for this error code
    pub fn category(&self) -> &'static str {
        match self {
            UnifiedError::Unauthorized | UnifiedError::InvalidRole | UnifiedError::RoleNotFound |
            UnifiedError::NotTrustedContract | UnifiedError::InsufficientPermissions | UnifiedError::AccessDenied => "authorization",
            
            UnifiedError::InvalidInput | UnifiedError::InvalidAmount | UnifiedError::InvalidAddress |
            UnifiedError::InvalidSignature | UnifiedError::InvalidTimestamp | UnifiedError::InvalidFormat |
            UnifiedError::MissingRequiredField | UnifiedError::OutOfBounds => "validation",
            
            UnifiedError::NotInitialized | UnifiedError::AlreadyInitialized | UnifiedError::NotFound |
            UnifiedError::AlreadyExists | UnifiedError::InvalidState | UnifiedError::StateTransition => "state",
            
            UnifiedError::Overflow | UnifiedError::Underflow | UnifiedError::DivisionByZero | UnifiedError::InvalidCalculation => "arithmetic",
            
            UnifiedError::StorageError | UnifiedError::DataCorrupted | UnifiedError::InsufficientStorage => "storage",
            
            UnifiedError::BusinessLogicError | UnifiedError::WorkflowError | UnifiedError::ConditionNotMet => "business_logic",
            
            UnifiedError::CheckpointNotFound | UnifiedError::RollbackDetected | UnifiedError::DoubleApplication | UnifiedError::CheckpointCorrupted => "checkpointing",
            
            UnifiedError::EmergencyMode | UnifiedError::Paused | UnifiedError::Halted | UnifiedError::CriticalError => "emergency",
            
            UnifiedError::ContractCallFailed | UnifiedError::InvalidContract | UnifiedError::ContractNotResponding => "cross_contract",
            
            UnifiedError::ProposalNotFound | UnifiedError::VotingPeriodEnded | UnifiedError::QuorumNotMet | UnifiedError::AlreadyVoted => "governance",
            
            UnifiedError::ClaimNotFound | UnifiedError::ClaimAlreadyProcessed | UnifiedError::EvidenceInvalid | UnifiedError::ClaimExpired => "claims",
            
            UnifiedError::PolicyNotFound | UnifiedError::PolicyExpired | UnifiedError::CoverageInsufficient | UnifiedError::PremiumNotPaid => "policy",
            
            UnifiedError::InsufficientLiquidity | UnifiedError::ProviderNotFound | UnifiedError::InsufficientStake | UnifiedError::LiquidityViolation => "risk_pool",
            
            UnifiedError::SlashConditionNotMet | UnifiedError::SlashingFailed | UnifiedError::StakeInsufficient => "slashing",
            
            UnifiedError::OracleUnavailable | UnifiedError::InvalidPriceData | UnifiedError::OracleSignatureInvalid | UnifiedError::PriceStale => "oracle",
            
            UnifiedError::AssetNotFound | UnifiedError::AssetAlreadyRegistered | UnifiedError::InvalidAsset => "asset_registry",
            
            UnifiedError::AuditLogFailed | UnifiedError::AuditRecordCorrupted => "audit_trail",
            
            UnifiedError::AlertFailed | UnifiedError::AlertConfigInvalid => "alerting",
            
            UnifiedError::MonitoringError | UnifiedError::MetricCollectionFailed => "monitoring",
        }
    }
    
    /// Get the severity level for this error
    pub fn severity(&self) -> &'static str {
        match self {
            UnifiedError::CriticalError | UnifiedError::RollbackDetected | UnifiedError::CheckpointCorrupted => "critical",
            UnifiedError::Unauthorized | UnifiedError::EmergencyMode | UnifiedError::Halted |
            UnifiedError::Overflow | UnifiedError::Underflow | UnifiedError::DataCorrupted => "high",
            UnifiedError::InvalidState | UnifiedError::BusinessLogicError | UnifiedError::WorkflowError |
            UnifiedError::ProposalNotFound | UnifiedError::QuorumNotMet => "medium",
            _ => "low",
        }
    }
    
    /// Get a suggested recovery action for this error
    pub fn recovery_action(&self) -> &'static str {
        match self {
            UnifiedError::Unauthorized => "Check permissions and ensure proper role assignment",
            UnifiedError::InvalidInput => "Validate input parameters and retry with correct values",
            UnifiedError::NotFound => "Ensure the resource exists before attempting to access it",
            UnifiedError::AlreadyExists => "Check if the operation was already completed",
            UnifiedError::Overflow => "Use smaller values or implement proper bounds checking",
            UnifiedError::Paused => "Wait for contract to be unpaused or contact admin",
            UnifiedError::InsufficientLiquidity => "Add more funds/liquidity or reduce operation amount",
            UnifiedError::RollbackDetected => "Verify system state and contact administrators if needed",
            _ => "Review error details and consult documentation",
        }
    }
}

/// Macro to convert contract-specific errors to UnifiedError
#[macro_export]
macro_rules! to_unified_error {
    ($error:expr) => {
        match $error {
            // Authorization errors
            crate::ContractError::Unauthorized => UnifiedError::Unauthorized,
            crate::ContractError::InvalidRole => UnifiedError::InvalidRole,
            crate::ContractError::RoleNotFound => UnifiedError::RoleNotFound,
            crate::ContractError::NotTrustedContract => UnifiedError::NotTrustedContract,
            
            // Validation errors
            crate::ContractError::InvalidInput => UnifiedError::InvalidInput,
            crate::ContractError::InvalidAmount => UnifiedError::InvalidAmount,
            
            // State errors
            crate::ContractError::NotInitialized => UnifiedError::NotInitialized,
            crate::ContractError::AlreadyInitialized => UnifiedError::AlreadyInitialized,
            crate::ContractError::NotFound => UnifiedError::NotFound,
            crate::ContractError::AlreadyExists => UnifiedError::AlreadyExists,
            crate::ContractError::InvalidState => UnifiedError::InvalidState,
            
            // Arithmetic errors
            crate::ContractError::Overflow => UnifiedError::Overflow,
            
            // Emergency errors
            crate::ContractError::Paused => UnifiedError::Paused,
            
            // Checkpointing errors
            crate::ContractError::CheckpointNotFound => UnifiedError::CheckpointNotFound,
            crate::ContractError::RollbackDetected => UnifiedError::RollbackDetected,
            crate::ContractError::DoubleApplication => UnifiedError::DoubleApplication,
            crate::ContractError::CheckpointCorrupted => UnifiedError::CheckpointCorrupted,
            
            // Default fallback
            _ => UnifiedError::BusinessLogicError,
        }
    };
}
'''
        return rust_code

def main():
    parser = argparse.ArgumentParser(description='Unified Error Code Catalog Generator')
    parser.add_argument('--contracts-dir', default='contracts', help='Contracts directory path')
    parser.add_argument('--output', default='error_codes.json', help='Output JSON file')
    parser.add_argument('--rust-output', help='Output Rust module file')
    parser.add_argument('--validate-only', action='store_true', help='Only validate existing catalog')
    parser.add_argument('--catalog', help='Existing catalog to validate')
    
    args = parser.parse_args()
    
    catalog = UnifiedErrorCatalog()
    
    if args.validate_only:
        if not args.catalog:
            print("Error: --catalog required when using --validate-only")
            return 1
        
        # Load existing catalog
        try:
            with open(args.catalog, 'r') as f:
                existing_data = json.load(f)
            
            # Reconstruct error codes from catalog
            for category, errors in existing_data.get('errors', {}).items():
                for key, error_data in errors.items():
                    error = ErrorCode(
                        name=error_data['name'],
                        code=error_data['code'],
                        category=ErrorCategory(category),
                        description=error_data['description'],
                        contract=error_data['contract'],
                        severity=error_data['severity'],
                        recovery_action=error_data.get('recovery_action')
                    )
                    catalog.error_codes[key] = error
                    catalog.contracts.add(error_data['contract'])
            
            issues = catalog.validate_error_codes()
            
            if issues:
                print(f"Found {len(issues)} validation issues:")
                for issue in issues:
                    print(f"  - {issue}")
                return 1
            else:
                print("No validation issues found!")
                return 0
                
        except Exception as e:
            print(f"Error loading catalog: {e}")
            return 1
    
    # Scan contracts directory
    catalog.scan_contracts_directory(args.contracts_dir)
    
    if not catalog.error_codes:
        print("No error codes found in contracts")
        return 1
    
    # Validate error codes
    issues = catalog.validate_error_codes()
    if issues:
        print(f"Found {len(issues)} validation issues:")
        for issue in issues:
            print(f"  - {issue}")
        print()
    
    # Generate catalog
    catalog_data = catalog.generate_catalog()
    
    # Save JSON catalog
    with open(args.output, 'w') as f:
        json.dump(catalog_data, f, indent=2)
    
    print(f"Error catalog saved to {args.output}")
    print(f"Found {len(catalog.error_codes)} error codes across {len(catalog.contracts)} contracts")
    
    # Generate Rust module if requested
    if args.rust_output:
        rust_code = catalog.generate_rust_module()
        with open(args.rust_output, 'w') as f:
            f.write(rust_code)
        print(f"Rust module saved to {args.rust_output}")
    
    return 0

if __name__ == '__main__':
    exit(main())
