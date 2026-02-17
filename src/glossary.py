"""Telecom RAG - Glossary Module

Provides telecom terminology expansion for query enhancement.
Based on 3GPP TR 21.905 vocabulary.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import GLOSSARY_DIR


# Core telecom glossary - essential terms from 3GPP TR 21.905
# This covers the most common acronyms and terms
TELECOM_GLOSSARY: Dict[str, str] = {
    # 5G/NR Terms
    "5G": "Fifth Generation mobile network technology",
    "NR": "New Radio - the 5G radio access technology defined by 3GPP",
    "gNB": "Next Generation NodeB - the 5G base station",
    "NGC": "Next Generation Core - the 5G core network",
    "5GC": "5G Core network",
    
    # LTE/4G Terms
    "LTE": "Long Term Evolution - 4G mobile broadband technology",
    "eNB": "Evolved NodeB - the LTE base station",
    "EPC": "Evolved Packet Core - the 4G core network",
    
    # Radio Access
    "HARQ": "Hybrid Automatic Repeat Request - combines forward error correction with ARQ for reliable data transmission",
    "MIMO": "Multiple Input Multiple Output - antenna technology using multiple antennas",
    "OFDM": "Orthogonal Frequency Division Multiplexing - modulation scheme",
    "OFDMA": "Orthogonal Frequency Division Multiple Access",
    "PDCP": "Packet Data Convergence Protocol",
    "PDSCH": "Physical Downlink Shared Channel",
    "PUSCH": "Physical Uplink Shared Channel",
    "PUCCH": "Physical Uplink Control Channel",
    "RLC": "Radio Link Control",
    "RRC": "Radio Resource Control",
    "RSRP": "Reference Signal Received Power - measurement of signal strength",
    "RSRQ": "Reference Signal Received Quality",
    "RSSI": "Received Signal Strength Indicator",
    "SINR": "Signal to Interference plus Noise Ratio",
    "SNR": "Signal to Noise Ratio",
    
    # Network Architecture
    "RAN": "Radio Access Network",
    "CN": "Core Network",
    "UE": "User Equipment - mobile device",
    "MME": "Mobility Management Entity",
    "SGW": "Serving Gateway",
    "PGW": "Packet Data Network Gateway",
    "AMF": "Access and Mobility Management Function",
    "SMF": "Session Management Function",
    "UPF": "User Plane Function",
    
    # Performance & KPIs
    "KPI": "Key Performance Indicator",
    "QoS": "Quality of Service",
    "QoE": "Quality of Experience",
    "BLER": "Block Error Rate",
    "BER": "Bit Error Rate",
    "PRB": "Physical Resource Block",
    "RB": "Resource Block",
    "CQI": "Channel Quality Indicator",
    "MCS": "Modulation and Coding Scheme",
    "VSWR": "Voltage Standing Wave Ratio - antenna measurement indicating impedance mismatch",
    
    # Spectrum & Bands
    "FDD": "Frequency Division Duplex",
    "TDD": "Time Division Duplex",
    "CA": "Carrier Aggregation",
    "DSS": "Dynamic Spectrum Sharing",
    "FR1": "Frequency Range 1 - sub-6 GHz bands for 5G",
    "FR2": "Frequency Range 2 - mmWave bands for 5G",
    "mmWave": "Millimeter Wave - high frequency bands above 24 GHz",
    
    # Protocols & Interfaces
    "SCTP": "Stream Control Transmission Protocol",
    "GTP": "GPRS Tunneling Protocol",
    "NGAP": "Next Generation Application Protocol",
    "XnAP": "Xn Application Protocol",
    "F1AP": "F1 Application Protocol",
    "E1AP": "E1 Application Protocol",
    "S1AP": "S1 Application Protocol",
    "X2AP": "X2 Application Protocol",
    
    # Network Operations
    "OSS": "Operations Support System",
    "BSS": "Business Support System",
    "SON": "Self-Organizing Network",
    "ANR": "Automatic Neighbor Relations",
    "MLB": "Mobility Load Balancing",
    "MRO": "Mobility Robustness Optimization",
    "CCO": "Coverage and Capacity Optimization",
    "PM": "Performance Management",
    "FM": "Fault Management",
    "CM": "Configuration Management",
    
    # Standards Bodies
    "3GPP": "3rd Generation Partnership Project - standards organization",
    "ETSI": "European Telecommunications Standards Institute",
    "ITU": "International Telecommunication Union",
    "IEEE": "Institute of Electrical and Electronics Engineers",
    
    # Specifications
    "TS": "Technical Specification",
    "TR": "Technical Report",
    "Release": "3GPP specification version grouping",
    
    # Network Slicing
    "NSSAI": "Network Slice Selection Assistance Information",
    "SST": "Slice/Service Type",
    "SD": "Slice Differentiator",
    
    # Security
    "AUSF": "Authentication Server Function",
    "SEAF": "Security Anchor Function",
    "UDM": "Unified Data Management",
    "NRF": "Network Repository Function",
}


class TelecomGlossary:
    """Telecom glossary for query enhancement."""
    
    def __init__(self, custom_glossary_path: Optional[Path] = None):
        self.glossary = TELECOM_GLOSSARY.copy()
        
        # Load custom glossary if provided
        if custom_glossary_path and custom_glossary_path.exists():
            self._load_custom_glossary(custom_glossary_path)
    
    def _load_custom_glossary(self, path: Path):
        """Load additional terms from JSON file."""
        try:
            with open(path, "r") as f:
                custom_terms = json.load(f)
                self.glossary.update(custom_terms)
            print(f"📖 Loaded {len(custom_terms)} custom glossary terms")
        except Exception as e:
            print(f"⚠️ Error loading custom glossary: {e}")
    
    def extract_terms(self, text: str) -> List[str]:
        """Extract telecom terms/acronyms from text."""
        # Find potential acronyms (2-6 uppercase letters)
        acronyms = re.findall(r'\b[A-Z]{2,6}\b', text)
        
        # Find terms that match glossary (case-insensitive)
        words = text.split()
        terms = []
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word).upper()
            if clean_word in self.glossary:
                terms.append(clean_word)
        
        # Also check for acronyms
        for acronym in acronyms:
            if acronym in self.glossary and acronym not in terms:
                terms.append(acronym)
        
        return list(set(terms))
    
    def get_definitions(self, terms: List[str]) -> Dict[str, str]:
        """Get definitions for a list of terms."""
        return {term: self.glossary.get(term, "") for term in terms if term in self.glossary}
    
    def enhance_query(self, query: str) -> Tuple[str, str]:
        """
        Enhance query with glossary definitions.
        
        Returns:
            Tuple of (enhanced_query, glossary_context)
        """
        # Extract terms from query
        terms = self.extract_terms(query)
        
        if not terms:
            return query, ""
        
        # Get definitions
        definitions = self.get_definitions(terms)
        
        # Build glossary context string
        glossary_lines = []
        for term, definition in definitions.items():
            glossary_lines.append(f"- {term}: {definition}")
        
        glossary_context = "\n".join(glossary_lines) if glossary_lines else ""
        
        # Build enhanced query (append definitions inline)
        enhanced_parts = []
        for term, definition in definitions.items():
            enhanced_parts.append(f"{term} ({definition})")
        
        enhanced_query = query
        for term in terms:
            if term in definitions:
                # Replace first occurrence with expanded form
                pattern = rf'\b{re.escape(term)}\b'
                replacement = f"{term} ({definitions[term]})"
                enhanced_query = re.sub(pattern, replacement, enhanced_query, count=1)
        
        return enhanced_query, glossary_context
    
    def save_glossary(self, filename: str = "telecom_glossary.json"):
        """Save current glossary to file."""
        output_path = GLOSSARY_DIR / filename
        
        with open(output_path, "w") as f:
            json.dump(self.glossary, f, indent=2)
        
        print(f"💾 Saved glossary with {len(self.glossary)} terms to {output_path}")
    
    def add_term(self, term: str, definition: str):
        """Add a new term to the glossary."""
        self.glossary[term.upper()] = definition


if __name__ == "__main__":
    # Test glossary
    glossary = TelecomGlossary()
    
    # Test query enhancement
    test_query = "What is the HARQ process in NR?"
    enhanced, context = glossary.enhance_query(test_query)
    
    print("Original query:", test_query)
    print("\nEnhanced query:", enhanced)
    print("\nGlossary context:")
    print(context)
    
    # Save glossary
    glossary.save_glossary()
