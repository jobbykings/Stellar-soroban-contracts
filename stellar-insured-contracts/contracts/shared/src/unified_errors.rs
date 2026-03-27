//! Unified Error Code Catalog for Stellar Soroban Contracts
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
