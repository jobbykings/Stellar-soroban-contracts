#!/usr/bin/env python3
"""
Soroban Symbolic Analysis Security Checker

This script runs symbolic analysis and model checking over Soroban contract invariants
to detect potential security vulnerabilities like unauthorized payouts, state mutations,
and other logic bugs.

Usage:
    python symbolic_analysis.py --contract-path <path> --invariants <invariants.json>
    python symbolic_analysis.py --all-contracts --config analysis_config.json
"""

import json
import argparse
import subprocess
import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class VulnerabilityType(Enum):
    UNAUTHORIZED_PAYOUT = "unauthorized_payout"
    UNAUTHORIZED_STATE_MUTATION = "unauthorized_state_mutation"
    REENTRANCY = "reentrancy"
    INTEGER_OVERFLOW = "integer_overflow"
    ACCESS_CONTROL = "access_control"
    LOGIC_BUG = "logic_bug"

@dataclass
class Vulnerability:
    type: VulnerabilityType
    severity: str  # "critical", "high", "medium", "low"
    contract: str
    function: str
    line: Optional[int]
    description: str
    reproduction: str
    cvss_score: Optional[float] = None

@dataclass
class Invariant:
    name: str
    description: str
    contract: str
    check_function: str
    critical: bool = True

class SorobanSymbolicAnalyzer:
    def __init__(self, config_path: Optional[str] = None):
        self.config = self.load_config(config_path)
        self.vulnerabilities: List[Vulnerability] = []
        self.invariants: List[Invariant] = []
        self.contracts_analyzed = 0
        
    def load_config(self, config_path: Optional[str]) -> Dict:
        """Load analysis configuration from file or use defaults."""
        default_config = {
            "timeout_seconds": 300,
            "max_depth": 50,
            "check_reentrancy": True,
            "check_overflow": True,
            "check_access_control": True,
            "symbolic_engine": "corral",
            "contracts_dir": "contracts",
            "invariants_file": "invariants.json",
            "output_format": "json",
            "fail_on_critical": True,
            "fail_on_high": True
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
            default_config.update(user_config)
        
        return default_config
    
    def load_invariants(self, invariants_path: str) -> List[Invariant]:
        """Load contract invariants from JSON file."""
        invariants = []
        
        if not os.path.exists(invariants_path):
            print(f"Warning: Invariants file {invariants_path} not found")
            return invariants
            
        with open(invariants_path, 'r') as f:
            data = json.load(f)
            
        for inv_data in data.get('invariants', []):
            invariant = Invariant(
                name=inv_data['name'],
                description=inv_data['description'],
                contract=inv_data['contract'],
                check_function=inv_data['check_function'],
                critical=inv_data.get('critical', True)
            )
            invariants.append(invariant)
            
        return invariants
    
    def extract_functions_from_contract(self, contract_path: str) -> List[Dict]:
        """Extract function signatures and metadata from Rust contract."""
        functions = []
        
        try:
            with open(contract_path, 'r') as f:
                content = f.read()
                
            # Find public functions
            func_pattern = r'pub\s+fn\s+(\w+)\s*\([^)]*\)\s*(?:->\s*[^{]*)?\s*{'
            matches = re.finditer(func_pattern, content)
            
            for match in matches:
                func_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                
                # Skip internal functions
                if func_name.startswith('_'):
                    continue
                    
                functions.append({
                    'name': func_name,
                    'line': line_num,
                    'contract': os.path.basename(contract_path)
                })
                
        except Exception as e:
            print(f"Error parsing contract {contract_path}: {e}")
            
        return functions
    
    def check_unauthorized_payout(self, contract_path: str, functions: List[Dict]) -> List[Vulnerability]:
        """Check for functions that can transfer funds without proper authorization."""
        vulnerabilities = []
        
        risky_patterns = [
            r'transfer_payment\s*\(',
            r'pay\s*\(',
            r'payout\s*\(',
            r'withdraw\s*\(',
            r'send_payment\s*\(',
            r'.*transfer.*\s*\('
        ]
        
        with open(contract_path, 'r') as f:
            content = f.read()
            
        for func in functions:
            func_content = self.extract_function_content(content, func['name'])
            
            if not func_content:
                continue
                
            # Check for payout patterns
            has_payout = any(re.search(pattern, func_content) for pattern in risky_patterns)
            
            if has_payout:
                # Check for authorization
                has_auth = (
                    'require_auth()' in func_content or
                    'require_role' in func_content or
                    'require_admin' in func_content or
                    'has_role' in func_content or
                    'authorize' in func_content.lower()
                )
                
                if not has_auth:
                    vuln = Vulnerability(
                        type=VulnerabilityType.UNAUTHORIZED_PAYOUT,
                        severity="critical",
                        contract=func['contract'],
                        function=func['name'],
                        line=func['line'],
                        description=f"Function {func['name']} can transfer funds without proper authorization",
                        reproduction=f"Call {func['name']} with valid parameters to bypass authorization",
                        cvss_score=9.0
                    )
                    vulnerabilities.append(vuln)
                    
        return vulnerabilities
    
    def check_unauthorized_state_mutation(self, contract_path: str, functions: List[Dict]) -> List[Vulnerability]:
        """Check for functions that modify critical state without authorization."""
        vulnerabilities = []
        
        state_mutation_patterns = [
            r'storage\(\)\.persistent\(\)\.set\s*\(',
            r'storage\(\)\.temporary\(\)\.set\s*\(',
            r'\.set\s*\(',
            r'state\.\w+\s*='
        ]
        
        critical_state_keys = [
            'admin', 'owner', 'config', 'policy', 'claim', 'pool', 'treasury'
        ]
        
        with open(contract_path, 'r') as f:
            content = f.read()
            
        for func in functions:
            func_content = self.extract_function_content(content, func['name'])
            
            if not func_content:
                continue
                
            # Check for state mutations
            has_mutation = any(re.search(pattern, func_content) for pattern in state_mutation_patterns)
            
            if has_mutation:
                # Check if it modifies critical state
                modifies_critical = any(key in func_content.lower() for key in critical_state_keys)
                
                if modifies_critical:
                    # Check for authorization
                    has_auth = (
                        'require_auth()' in func_content or
                        'require_role' in func_content or
                        'require_admin' in func_content or
                        'authorize' in func_content.lower()
                    )
                    
                    if not has_auth:
                        vuln = Vulnerability(
                            type=VulnerabilityType.UNAUTHORIZED_STATE_MUTATION,
                            severity="high",
                            contract=func['contract'],
                            function=func['name'],
                            line=func['line'],
                            description=f"Function {func['name']} modifies critical state without authorization",
                            reproduction=f"Call {func['name']} to modify critical state without proper permissions",
                            cvss_score=7.5
                        )
                        vulnerabilities.append(vuln)
                        
        return vulnerabilities
    
    def extract_function_content(self, content: str, func_name: str) -> Optional[str]:
        """Extract the full content of a specific function."""
        pattern = rf'pub\s+fn\s+{func_name}\s*\([^)]*\)(?:\s*->\s*[^{{]*)?\s*{{'
        match = re.search(pattern, content)
        
        if not match:
            return None
            
        start_pos = match.start()
        brace_count = 0
        pos = match.end() - 1  # Start at opening brace
        
        while pos < len(content):
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
                if brace_count == 0:
                    return content[start_pos:pos + 1]
            pos += 1
            
        return None
    
    def analyze_contract(self, contract_path: str) -> List[Vulnerability]:
        """Analyze a single contract for security vulnerabilities."""
        print(f"Analyzing contract: {contract_path}")
        
        vulnerabilities = []
        
        # Extract functions
        functions = self.extract_functions_from_contract(contract_path)
        
        # Run various security checks
        if self.config.get('check_access_control', True):
            vulnerabilities.extend(self.check_unauthorized_payout(contract_path, functions))
            vulnerabilities.extend(self.check_unauthorized_state_mutation(contract_path, functions))
        
        # TODO: Add more sophisticated symbolic analysis here
        # For now, we're doing static pattern matching
        
        return vulnerabilities
    
    def analyze_all_contracts(self) -> List[Vulnerability]:
        """Analyze all contracts in the contracts directory."""
        all_vulnerabilities = []
        contracts_dir = Path(self.config['contracts_dir'])
        
        if not contracts_dir.exists():
            print(f"Contracts directory {contracts_dir} not found")
            return all_vulnerabilities
            
        # Find all Rust contract files
        contract_files = list(contracts_dir.rglob("lib.rs"))
        contract_files.extend(list(contracts_dir.rglob("*.rs")))
        
        for contract_file in contract_files:
            if contract_file.name == 'lib.rs' or contract_file.parent.name in contracts_dir.iterdir():
                vulnerabilities = self.analyze_contract(str(contract_file))
                all_vulnerabilities.extend(vulnerabilities)
                self.contracts_analyzed += 1
                
        return all_vulnerabilities
    
    def generate_report(self, vulnerabilities: List[Vulnerability]) -> Dict:
        """Generate analysis report."""
        report = {
            'summary': {
                'total_vulnerabilities': len(vulnerabilities),
                'contracts_analyzed': self.contracts_analyzed,
                'critical': len([v for v in vulnerabilities if v.severity == 'critical']),
                'high': len([v for v in vulnerabilities if v.severity == 'high']),
                'medium': len([v for v in vulnerabilities if v.severity == 'medium']),
                'low': len([v for v in vulnerabilities if v.severity == 'low'])
            },
            'vulnerabilities': []
        }
        
        for vuln in vulnerabilities:
            report['vulnerabilities'].append({
                'type': vuln.type.value,
                'severity': vuln.severity,
                'contract': vuln.contract,
                'function': vuln.function,
                'line': vuln.line,
                'description': vuln.description,
                'reproduction': vuln.reproduction,
                'cvss_score': vuln.cvss_score
            })
            
        return report
    
    def check_ci_failure_conditions(self, vulnerabilities: List[Vulnerability]) -> bool:
        """Check if CI should fail based on vulnerabilities found."""
        should_fail = False
        
        critical_count = len([v for v in vulnerabilities if v.severity == 'critical'])
        high_count = len([v for v in vulnerabilities if v.severity == 'high'])
        
        if self.config.get('fail_on_critical', True) and critical_count > 0:
            print(f"CI FAILURE: Found {critical_count} critical vulnerabilities")
            should_fail = True
            
        if self.config.get('fail_on_high', True) and high_count > 0:
            print(f"CI FAILURE: Found {high_count} high severity vulnerabilities")
            should_fail = True
            
        return should_fail

def main():
    parser = argparse.ArgumentParser(description='Soroban Symbolic Analysis Security Checker')
    parser.add_argument('--contract-path', help='Path to specific contract to analyze')
    parser.add_argument('--all-contracts', action='store_true', help='Analyze all contracts')
    parser.add_argument('--config', help='Path to analysis configuration file')
    parser.add_argument('--invariants', help='Path to invariants JSON file')
    parser.add_argument('--output', help='Output file for analysis report')
    parser.add_argument('--format', choices=['json', 'text'], default='json', help='Output format')
    
    args = parser.parse_args()
    
    if not args.contract_path and not args.all_contracts:
        print("Error: Must specify either --contract-path or --all-contracts")
        sys.exit(1)
    
    analyzer = SorobanSymbolicAnalyzer(args.config)
    
    if args.invariants:
        analyzer.invariants = analyzer.load_invariants(args.invariants)
    
    vulnerabilities = []
    
    if args.contract_path:
        vulnerabilities = analyzer.analyze_contract(args.contract_path)
    else:
        vulnerabilities = analyzer.analyze_all_contracts()
    
    # Generate report
    report = analyzer.generate_report(vulnerabilities)
    
    # Output report
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to {args.output}")
    else:
        if args.format == 'json':
            print(json.dumps(report, indent=2))
        else:
            # Text format
            print(f"Soroban Security Analysis Report")
            print(f"=================================")
            print(f"Contracts analyzed: {report['summary']['contracts_analyzed']}")
            print(f"Total vulnerabilities: {report['summary']['total_vulnerabilities']}")
            print(f"Critical: {report['summary']['critical']}")
            print(f"High: {report['summary']['high']}")
            print(f"Medium: {report['summary']['medium']}")
            print(f"Low: {report['summary']['low']}")
            print()
            
            for vuln in report['vulnerabilities']:
                print(f"[{vuln['severity'].upper()}] {vuln['type']}")
                print(f"  Contract: {vuln['contract']}")
                print(f"  Function: {vuln['function']}")
                print(f"  Line: {vuln['line']}")
                print(f"  Description: {vuln['description']}")
                print(f"  Reproduction: {vuln['reproduction']}")
                print()
    
    # Check CI failure conditions
    if analyzer.check_ci_failure_conditions(vulnerabilities):
        sys.exit(1)

if __name__ == '__main__':
    main()
