"""Telecom RAG - Data Loader Module

Handles loading and processing of telecom documents:
- TeleQnA dataset from HuggingFace
- PDF documents (3GPP specs)
- CSV data (KPIs)
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import tiktoken

from tqdm import tqdm

from .config import (
    RAW_DATA_DIR, 
    PROCESSED_DATA_DIR, 
    CHUNK_SIZE, 
    CHUNK_OVERLAP
)


@dataclass
class Document:
    """Represents a processed document chunk."""
    content: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {"content": self.content, "metadata": self.metadata}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        return cls(content=data["content"], metadata=data["metadata"])


class TelecomDataLoader:
    """Load and process telecom documents for RAG."""
    
    def __init__(self):
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.documents: List[Document] = []
        
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.tokenizer.encode(text))
    
    def normalize_category(self, raw_category: str) -> str:
        """
        Normalize category to supported subset:
        - standards
        - network_operations
        - performance
        - architecture
        - general
        """
        cat = raw_category.lower()
        
        # Standards
        if any(x in cat for x in ['3gpp', 'standard', 'spec', 'protocol', 'compliance', 'release']):
            return 'standards'
            
        # Network Operations
        if any(x in cat for x in ['operation', 'maintain', 'troubleshoot', 'fault', 'alarm', 'config', 'radio', 'spectrum']):
            return 'network_operations'
            
        # Performance
        if any(x in cat for x in ['perform', 'kpi', 'optimiz', 'quality', 'throughput', 'latency']):
            return 'performance'
            
        # Architecture
        if any(x in cat for x in ['architect', 'fundament', 'concept', 'define', 'definition', 'core', 'ran']):
            return 'architecture'
            
        return 'general'
    
    def get_chunk_size_for_category(self, category: str) -> int:
        """
        Get optimal chunk size based on category (Architecture Spec 3.3).
        """
        cat = self.normalize_category(category)
        
        if cat == 'performance': 
            return 500 # Time-series data needs more context
        elif cat == 'network_operations': # alarms/troubleshooting
            return 250 # Event-based data
        elif cat == 'maintenance':
            return 300 # Task-based procedures
        elif cat == 'customer':
            return 400 # Entity-centric data
        
        # Default for standards/config/architecture
        return CHUNK_SIZE # 125 tokens

    def chunk_text(self, text: str, source: str, category: str) -> List[Document]:
        """Split text into chunks with category-specific sizing."""
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        # Determine chunk size dynamically
        chunk_size = self.get_chunk_size_for_category(category)
        overlap = CHUNK_OVERLAP
        
        start = 0
        chunk_idx = 0
        
        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            chunks.append(Document(
                content=chunk_text.strip(),
                metadata={
                    "source": source,
                    "category": self.normalize_category(category),
                    "chunk_index": chunk_idx,
                    "token_count": len(chunk_tokens)
                }
            ))
            
            start = end - CHUNK_OVERLAP if end < len(tokens) else end
            chunk_idx += 1
            
        return chunks
    
    def load_teleqna_dataset(self) -> List[Document]:
        """Load TeleQnA dataset from HuggingFace (requires HF_TOKEN for gated access)."""
        try:
            import os
            import pandas as pd
            from huggingface_hub import login
            
            # Check for HuggingFace token
            hf_token = os.getenv("HF_TOKEN")
            
            if hf_token and hf_token != "your_huggingface_token_here":
                print("🔐 Authenticating with HuggingFace...")
                login(token=hf_token, add_to_git_credential=False)
                print("✅ HuggingFace authentication successful")
            else:
                print("⚠️ No HF_TOKEN found in .env file")
                print("   To load TeleQnA dataset:")
                print("   1. Get token: https://huggingface.co/settings/tokens")
                print("   2. Request access: https://huggingface.co/datasets/netop/TeleQnA")
                print("   3. Add HF_TOKEN=your_token to .env file")
                raise ValueError("HF_TOKEN required for gated dataset")
            
            print("📡 Loading TeleQnA dataset from HuggingFace...")
            
            # Load using pandas as recommended by HuggingFace
            df = pd.read_json("hf://datasets/netop/TeleQnA/test.json")
            print(f"   Loaded {len(df)} records from TeleQnA")
            print(f"   Columns: {list(df.columns)}")
            
            documents = []
            skipped = 0
            
            for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing TeleQnA"):
                try:
                    # Extract question
                    question = row.get("question", "")
                    if not question:
                        skipped += 1
                        continue
                    
                    # TeleQnA structure: 
                    # - question: the question text
                    # - choices: list of options (strings)
                    # - answer: integer index of correct choice
                    # - subject: category/topic
                    # - explaination: explanation text (note: typo in dataset)
                    
                    choices = row.get("choices", [])
                    answer_idx = row.get("answer", None)
                    explanation = row.get("explaination", "") or row.get("explanation", "")
                    subject = row.get("subject", "telecom")
                    
                    # Build answer from correct choice + explanation
                    answer = ""
                    
                    if choices and answer_idx is not None:
                        try:
                            if isinstance(answer_idx, (int, float)) and 0 <= int(answer_idx) < len(choices):
                                correct_choice = choices[int(answer_idx)]
                                answer = f"{correct_choice}"
                                if explanation and len(explanation) > 10:
                                    answer += f"\n\nExplanation: {explanation}"
                        except (ValueError, IndexError, TypeError):
                            pass
                    
                    # Fallback to explanation only if no choice extracted
                    if not answer and explanation:
                        answer = explanation
                    
                    # Skip if no meaningful answer
                    if not answer or len(str(answer).strip()) < 5:
                        skipped += 1
                        continue
                    
                    # Combine Q&A as document content
                    content = f"Question: {question}\n\nAnswer: {answer}"
                    
                    doc = Document(
                        content=content,
                        metadata={
                            "source": "TeleQnA",
                            "category": self.normalize_category(str(subject) if subject else "telecom"),
                            "question": question,
                            "doc_id": f"teleqna_{idx}"
                        }
                    )
                    documents.append(doc)
                    
                except Exception as item_error:
                    if idx < 3:
                        print(f"   Error on item {idx}: {item_error}")
                    skipped += 1
                    continue
            
            if skipped > 0:
                print(f"   ⚠️ Skipped {skipped} items with issues")
            
            print(f"✅ Loaded {len(documents)} Q&A pairs from TeleQnA")
            return documents
            
        except Exception as e:
            print(f"⚠️ TeleQnA unavailable: {e}")
            print("   Falling back to public 3GPP-QA dataset...")
            return self.load_3gpp_qa_dataset()
    
    def load_3gpp_qa_dataset(self) -> List[Document]:
        """Load public 3GPP QA dataset from HuggingFace."""
        try:
            from datasets import load_dataset
            
            print("📡 Loading 3GPP-QA dataset from HuggingFace...")
            dataset = load_dataset("dinho1597/3GPP-QA-MultipleChoice", split="train")
            
            documents = []
            empty_count = 0
            
            for idx, item in enumerate(tqdm(dataset, desc="Processing 3GPP-QA")):
                question = item.get("question", "")
                
                # Try multiple ways to get the answer
                answer = ""
                
                # Method 1: Get from 'choices' list using 'answer' index
                choices = item.get("choices", [])
                answer_idx = item.get("answer", None)
                
                if choices and answer_idx is not None:
                    # answer_idx might be int or string
                    try:
                        if isinstance(answer_idx, int) and answer_idx < len(choices):
                            answer = choices[answer_idx]
                        elif isinstance(answer_idx, str):
                            # Try to find matching choice
                            for choice in choices:
                                if choice.strip().lower().startswith(answer_idx.lower()):
                                    answer = choice
                                    break
                            if not answer and answer_idx in ['A', 'B', 'C', 'D']:
                                idx_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
                                if idx_map.get(answer_idx, 0) < len(choices):
                                    answer = choices[idx_map[answer_idx]]
                    except:
                        pass
                
                # Method 2: Direct answer field
                if not answer:
                    answer = item.get("answer_text", "") or item.get("correct_answer", "")
                
                # Method 3: Include all choices as context if no clear answer
                if not answer and choices:
                    answer = "Possible answers: " + " | ".join(choices)
                
                # Skip if still no meaningful content
                if not answer or answer.strip() == "":
                    empty_count += 1
                    continue
                
                content = f"Question: {question}\n\nAnswer: {answer}"
                
                doc = Document(
                    content=content,
                    metadata={
                        "source": "3GPP-QA",
                        "category": self.normalize_category("3gpp_standards"),
                        "question": question,
                        "doc_id": f"3gpp_qa_{idx}"
                    }
                )
                documents.append(doc)
            
            if empty_count > 0:
                print(f"⚠️ Skipped {empty_count} entries with empty answers")
            
            if len(documents) < 100:
                print(f"⚠️ Only {len(documents)} valid Q&A pairs - data quality issue detected")
                print("   Will supplement with built-in knowledge base...")
            else:
                print(f"✅ Loaded {len(documents)} Q&A pairs from 3GPP-QA")
            
            return documents
            
        except Exception as e:
            print(f"⚠️ 3GPP-QA unavailable: {e}")
            print("   Using built-in telecom knowledge base...")
            return []
    
    def load_5g_faults_full_dataset(self) -> List[Document]:
        """Load 5G_Faults_Full dataset from HuggingFace - comprehensive fault Q&A."""
        try:
            from datasets import load_dataset
            
            print("📡 Loading 5G_Faults_Full dataset...")
            dataset = load_dataset("greenwich157/5G_Faults_Full", split="train")
            
            documents = []
            for idx, item in enumerate(tqdm(dataset, desc="Processing 5G Faults")):
                instruction = item.get("instruction", "")
                input_text = item.get("input", "")
                output = item.get("output", "")
                
                if not output or len(output.strip()) < 20:
                    continue
                
                # Combine into Q&A format
                question = instruction
                if input_text:
                    question = f"{instruction}\n\nContext: {input_text}"
                
                content = f"Question: {question}\n\nAnswer: {output}"
                
                doc = Document(
                    content=content,
                    metadata={
                        "source": "5G_Faults_Full",
                        "category": self.normalize_category("network_operations"),
                        "question": instruction[:200],
                        "doc_id": f"5g_fault_{idx}"
                    }
                )
                documents.append(doc)
            
            print(f"✅ Loaded {len(documents)} fault Q&A pairs from 5G_Faults_Full")
            return documents
            
        except Exception as e:
            print(f"⚠️ 5G_Faults_Full unavailable: {e}")
            return []
    
    def load_fault_troubleshooting_dataset(self) -> List[Document]:
        """Load telco-5G-data-faults dataset - symptoms, causes, actions."""
        try:
            from datasets import load_dataset
            import re
            
            print("📡 Loading telco-5G-data-faults dataset...")
            dataset = load_dataset("greenwich157/telco-5G-data-faults", split="train")
            
            documents = []
            for idx, item in enumerate(tqdm(dataset, desc="Processing Fault Troubleshooting")):
                text = item.get("text", "")
                
                if not text or len(text) < 50:
                    continue
                
                # Parse the structured format
                # Format: [SYSTEM]:... [SYMPTOMS]:... [CAUSES]:... [ACTIONS]:...
                symptoms = ""
                causes = ""
                actions = ""
                
                sym_match = re.search(r"\[SYMPTOMS\]:\s*'([^']+)'", text)
                cause_match = re.search(r"\[CAUSES\]:\s*'([^']+)'", text)
                action_match = re.search(r"\[ACTIONS\]:\s*'([^']+)'", text)
                
                if sym_match:
                    symptoms = sym_match.group(1)
                if cause_match:
                    causes = cause_match.group(1)
                if action_match:
                    actions = action_match.group(1)
                
                if not symptoms or not actions:
                    # Fallback: use full text
                    content = f"Fault Analysis:\n\n{text}"
                else:
                    content = f"""Fault Troubleshooting Guide

**Symptoms:** {symptoms}

**Root Causes:** {causes}

**Recommended Actions:** {actions}"""
                
                doc = Document(
                    content=content,
                    metadata={
                        "source": "telco-5G-data-faults",
                        "category": self.normalize_category("troubleshooting"),
                        "symptoms": symptoms[:100] if symptoms else "",
                        "doc_id": f"fault_ts_{idx}"
                    }
                )
                documents.append(doc)
            
            print(f"✅ Loaded {len(documents)} troubleshooting guides")
            return documents
            
        except Exception as e:
            print(f"⚠️ telco-5G-data-faults unavailable: {e}")
            return []
    
    def load_builtin_knowledge_base(self) -> List[Document]:
        """Load comprehensive built-in telecom knowledge base."""
        print("📚 Loading built-in telecom knowledge base...")
        
        # Comprehensive telecom knowledge covering all major areas
        knowledge_base = [
            # 5G NR Fundamentals
            {
                "content": """Question: What is 5G NR (New Radio)?

Answer: 5G NR (New Radio) is the global standard for a unified, more capable 5G wireless air interface. It was developed by 3GPP and delivers significantly faster speeds, lower latency, and greater capacity than previous generations. 5G NR operates in two frequency ranges: FR1 (sub-6 GHz, 410 MHz to 7.125 GHz) and FR2 (mmWave, 24.25 GHz to 52.6 GHz).

Key features include:
- Enhanced Mobile Broadband (eMBB) for high-speed data
- Ultra-Reliable Low-Latency Communications (URLLC) for mission-critical applications
- Massive Machine-Type Communications (mMTC) for IoT
- Flexible numerology with scalable subcarrier spacing (15, 30, 60, 120, 240 kHz)
- Advanced MIMO and beamforming capabilities

[Source: 3GPP TS 38.300 - NR Overall Description]""",
                "category": "architecture",
                "source": "3GPP_TS_38.300"
            },
            {
                "content": """Question: What is HARQ in 5G NR?

Answer: HARQ (Hybrid Automatic Repeat Request) is a combination of high-rate forward error correction (FEC) and ARQ error-control. In 5G NR, HARQ provides reliable data transmission by:

1. Using incremental redundancy - additional parity bits are sent if initial transmission fails
2. Soft combining - receiver combines information from failed and retransmitted packets
3. Asynchronous HARQ on uplink, synchronous on downlink
4. Up to 16 parallel HARQ processes in NR (vs 8 in LTE)
5. Faster retransmission times due to flexible slot structure

The HARQ process in NR supports:
- Variable retransmission timing
- Code Block Group (CBG) based retransmission for efficiency
- Flexible feedback timing with HARQ-ACK

[Source: 3GPP TS 38.321 - NR MAC Protocol]""",
                "category": "network_operations",
                "source": "3GPP_TS_38.321"
            },
            {
                "content": """Question: What is MIMO technology in telecom?

Answer: MIMO (Multiple-Input Multiple-Output) is a wireless technology that uses multiple antennas at transmitter and receiver to improve communication performance. In 5G NR, Massive MIMO is a key feature:

Types of MIMO:
- SU-MIMO (Single-User): Multiple streams to one user
- MU-MIMO (Multi-User): Simultaneous transmission to multiple users
- Massive MIMO: Large antenna arrays (64-256+ elements)

Benefits:
- Increased spectral efficiency
- Higher data rates through spatial multiplexing
- Better coverage through beamforming
- Improved reliability through spatial diversity

5G NR supports up to 8 layers for downlink and 4 layers for uplink MIMO transmission.

[Source: 3GPP TS 38.211 - NR Physical Channels and Modulation]""",
                "category": "network_operations",
                "source": "3GPP_TS_38.211"
            },
            # Network Architecture
            {
                "content": """Question: What is the difference between gNB and eNB?

Answer: gNB (gNodeB) and eNB (eNodeB) are base station types for different generations:

gNB (5G NR Base Station):
- Part of 5G New Radio (NR) access network
- Connects to 5G Core (5GC) via NG interface
- Supports NR radio protocols
- Can operate in Standalone (SA) or Non-Standalone (NSA) mode
- Connects to other gNBs via Xn interface

eNB (LTE Base Station):
- Part of 4G LTE E-UTRAN
- Connects to EPC (Evolved Packet Core) via S1 interface
- Supports LTE radio protocols
- Connects to other eNBs via X2 interface

In NSA mode, gNB can connect to eNB for combined LTE/NR operation using EN-DC (E-UTRA-NR Dual Connectivity).

[Source: 3GPP TS 38.401 - NG-RAN Architecture]""",
                "category": "architecture",
                "source": "3GPP_TS_38.401"
            },
            {
                "content": """Question: What is 5G Core (5GC) architecture?

Answer: 5G Core (5GC) is the service-based architecture for 5G networks. Key network functions include:

Core Network Functions:
- AMF (Access and Mobility Management Function): Registration, connection, mobility
- SMF (Session Management Function): Session establishment, modification
- UPF (User Plane Function): Packet routing, forwarding, QoS
- UDM (Unified Data Management): Subscription data, authentication
- AUSF (Authentication Server Function): Security procedures
- NRF (Network Repository Function): Service discovery
- PCF (Policy Control Function): Policy rules
- NSSF (Network Slice Selection Function): Slice assignment

Key Characteristics:
- Service-Based Interface (SBI) using HTTP/2 and REST
- Control and User Plane Separation (CUPS)
- Network slicing support
- Edge computing integration

[Source: 3GPP TS 23.501 - System Architecture for 5G]""",
                "category": "architecture",
                "source": "3GPP_TS_23.501"
            },
            # Network Operations
            {
                "content": """Question: How to troubleshoot VSWR alarm on cell site?

Answer: VSWR (Voltage Standing Wave Ratio) alarm indicates impedance mismatch in the antenna system. Troubleshooting steps:

1. Check VSWR Value:
   - Normal: < 1.5:1
   - Warning: 1.5:1 - 2.0:1
   - Critical: > 2.0:1

2. Common Causes:
   - Loose or damaged connector
   - Water ingress in connector or cable
   - Damaged feeder cable
   - Faulty antenna element
   - Lightning damage

3. Troubleshooting Steps:
   a) Verify alarm on OSS/NMS
   b) Check connector tightness at RRU and antenna
   c) Inspect for water damage using moisture indicators
   d) Perform line sweep test with site analyzer
   e) Check for cable kinks or damage
   f) Verify antenna grounding

4. Resolution:
   - Replace damaged connector with weatherproofing
   - Replace damaged cable section
   - If antenna damaged, arrange replacement
   - Document and close ticket

[Source: Vendor Maintenance Manual - RAN Equipment]""",
                "category": "network_operations",
                "source": "Maintenance_Manual"
            },
            {
                "content": """Question: What KPIs should be monitored for 5G network quality?

Answer: Key Performance Indicators (KPIs) for 5G network quality include:

Accessibility KPIs:
- RRC Setup Success Rate (target: >99%)
- E-RAB/DRB Setup Success Rate (target: >99%)
- Registration Success Rate

Retainability KPIs:
- Call Drop Rate (target: <1%)
- RRC Abnormal Release Rate
- Session Drop Rate

Mobility KPIs:
- Handover Success Rate (target: >98%)
- Intra-frequency HO Success Rate
- Inter-RAT HO Success Rate

Integrity KPIs:
- Average Throughput (DL/UL)
- Latency (target: <10ms for eMBB, <1ms for URLLC)
- Packet Loss Rate
- BLER (Block Error Rate)

Availability KPIs:
- Cell Availability (target: >99.9%)
- Equipment Failure Rate

Traffic KPIs:
- PRB Utilization
- Active Users
- Data Volume (GB)

[Source: 3GPP TS 32.425 - Performance Measurements]""",
                "category": "performance",
                "source": "3GPP_TS_32.425"
            },
            # Spectrum and Bands
            {
                "content": """Question: What spectrum bands are used for 5G FR1?

Answer: 5G FR1 (Frequency Range 1) covers sub-6 GHz spectrum from 410 MHz to 7.125 GHz. Key bands include:

Low-Band (Coverage Layer):
- n5 (850 MHz): Wide area coverage
- n8 (900 MHz): Extended range
- n28 (700 MHz): APT band, excellent indoor penetration
- n71 (600 MHz): US-specific, great coverage

Mid-Band (Capacity Layer):
- n1 (2100 MHz): Traditional 3G/4G refarming
- n3 (1800 MHz): Widely deployed globally
- n7 (2600 MHz): TDD and FDD variants
- n41 (2500 MHz): TDD band, Sprint legacy
- n77 (3300-4200 MHz): C-Band, primary 5G capacity band
- n78 (3300-3800 MHz): C-Band subset
- n79 (4400-5000 MHz): Higher C-Band

Deployment Considerations:
- Low-band for coverage, mid-band for capacity
- Typical channel bandwidth: 20-100 MHz
- 3GPP mandates n78 support for NR devices

[Source: 3GPP TS 38.101-1 - NR User Equipment Radio Requirements]""",
                "category": "network_operations",
                "source": "3GPP_TS_38.101-1"
            },
            {
                "content": """Question: What is Carrier Aggregation in 5G?

Answer: Carrier Aggregation (CA) combines multiple component carriers (CCs) to increase bandwidth and data rates. In 5G NR:

Types of Carrier Aggregation:
- Intra-band contiguous: Adjacent carriers in same band
- Intra-band non-contiguous: Same band, separated carriers
- Inter-band: Different frequency bands combined

5G NR CA Capabilities:
- Up to 16 component carriers (3GPP Release 15+)
- Maximum aggregated bandwidth: 1 GHz in FR1, 2 GHz in FR2
- Each CC can be up to 100 MHz (FR1) or 400 MHz (FR2)

Configuration Examples:
- 2CC CA: n78+n78 (200 MHz)
- 3CC CA: n28+n78+n78 (coverage + capacity)
- EN-DC: LTE anchor + NR secondary

Benefits:
- Higher peak data rates
- Improved user experience
- Better spectrum utilization

[Source: 3GPP TS 38.101-1 - NR Radio Requirements]""",
                "category": "network_operations",
                "source": "3GPP_TS_38.101-1"
            },
            # Compliance and Standards
            {
                "content": """Question: What are the key features of 3GPP Release 17?

Answer: 3GPP Release 17 (frozen March 2022) introduced several enhancements:

New Features:
1. NR-Light (RedCap): Reduced Capability devices for IoT
   - Lower cost, smaller form factor
   - 20 MHz max bandwidth (vs 100 MHz for Full NR)
   
2. NR NTN (Non-Terrestrial Networks):
   - Satellite communication support
   - LEO and GEO satellite integration
   
3. Enhanced MIMO:
   - Up to 8Tx for uplink
   - Multi-TRP (Transmission Reception Point) enhancements
   
4. Coverage Enhancements:
   - PUSCH/PUCCH repetition
   - Improved cell edge performance
   
5. Sidelink Improvements:
   - Enhanced V2X for automotive
   - Improved reliability and latency
   
6. Positioning Enhancements:
   - Sub-meter accuracy improvements
   - Industrial IoT use cases

7. IIoT and URLLC:
   - TSC (Time-Sensitive Communication)
   - Enhanced scheduling

[Source: 3GPP Release 17 Description]""",
                "category": "standards",
                "source": "3GPP_Release_17"
            },
            {
                "content": """Question: What is Network Slicing in 5G?

Answer: Network Slicing allows operators to create multiple virtual networks on shared physical infrastructure:

Key Concepts:
- NSSAI (Network Slice Selection Assistance Information)
- S-NSSAI = SST (Slice/Service Type) + SD (Slice Differentiator)
- Standardized SST values:
  - SST 1: eMBB (enhanced Mobile Broadband)
  - SST 2: URLLC (Ultra-Reliable Low-Latency)
  - SST 3: mMTC (massive Machine-Type Communications)
  - SST 4: V2X (Vehicle-to-Everything)

Slice Components:
- RAN slice: Radio resource partitioning
- Core slice: Dedicated NFs per slice
- Transport slice: Network path isolation

Benefits:
- Customized QoS per service type
- Resource isolation and SLA guarantee
- Efficient resource utilization
- Service-specific optimization

Use Cases:
- Industrial automation (URLLC slice)
- Video streaming (eMBB slice)
- Smart meters (mMTC slice)

[Source: 3GPP TS 23.501 - System Architecture]""",
                "category": "standards",
                "source": "3GPP_TS_23.501"
            },
            # More operational content
            {
                "content": """Question: What is RRC connection and its states in 5G NR?

Answer: RRC (Radio Resource Control) manages the connection between UE and gNB. In 5G NR, there are three RRC states:

1. RRC_IDLE:
   - No RRC connection exists
   - UE monitors paging channel
   - Cell selection/reselection by UE
   - Minimal network resource usage
   - DRX for power saving

2. RRC_INACTIVE (New in NR):
   - RRC connection suspended, not released
   - UE context stored in network
   - Faster transition to connected state
   - RNA (RAN Notification Area) based mobility
   - Ideal for IoT devices with sporadic traffic

3. RRC_CONNECTED:
   - Active RRC connection
   - Network controls mobility (handovers)
   - Data transmission possible
   - UE measurements reported to network

State Transitions:
- IDLE → CONNECTED: RRC Setup procedure
- CONNECTED → INACTIVE: RRC Suspend
- INACTIVE → CONNECTED: RRC Resume (faster than Setup)
- CONNECTED → IDLE: RRC Release

[Source: 3GPP TS 38.331 - NR RRC Protocol]""",
                "category": "standards",
                "source": "3GPP_TS_38.331"
            },
            {
                "content": """Question: How does 5G beamforming work?

Answer: Beamforming in 5G NR uses antenna arrays to focus radio signals in specific directions:

Types of Beamforming:
1. Analog Beamforming:
   - Phase shifters in RF domain
   - Single beam at a time
   - Lower cost, limited flexibility

2. Digital Beamforming:
   - Baseband processing per antenna
   - Multiple beams simultaneously
   - Higher cost, maximum flexibility

3. Hybrid Beamforming (5G NR typical):
   - Combines analog and digital
   - Balance of cost and performance
   - Essential for mmWave (FR2)

Beam Management Procedures:
- P1: Beam sweeping for initial access (SSB beams)
- P2: Beam refinement at gNB
- P3: UE beam adjustment
- Beam failure recovery

SSB Beam Configuration:
- FR1: Up to 8 SSB beams
- FR2: Up to 64 SSB beams

Benefits:
- Extended range (10-15 dB gain)
- Improved interference management
- Higher spectral efficiency
- Essential for mmWave frequencies

[Source: 3GPP TS 38.214 - NR Physical Layer Procedures]""",
                "category": "network_operations",
                "source": "3GPP_TS_38.214"
            },
            # Capacity Planning
            {
                "content": """Question: How to calculate 5G cell capacity?

Answer: 5G cell capacity depends on multiple factors:

Capacity Formula:
Throughput = Bandwidth × Spectral Efficiency × MIMO Layers × (1 - Overhead)

Key Parameters:
1. Bandwidth: 20-100 MHz (FR1), up to 400 MHz (FR2)
2. Spectral Efficiency: 7-9 bps/Hz peak (256QAM)
3. MIMO Layers: Up to 8 DL, 4 UL
4. Overhead: ~25% (control channels, reference signals)

Capacity Planning Steps:
1. Traffic Demand Analysis:
   - Forecast user growth
   - Analyze traffic patterns
   - Consider busy hour factor (BHF)

2. Coverage Analysis:
   - Link budget calculation
   - Site density requirements
   - Indoor coverage needs

3. Capacity Dimensioning:
   - PRB utilization threshold (typically 70%)
   - User throughput requirements
   - QoS class distribution

4. Spectrum Strategy:
   - Band combination planning
   - Carrier aggregation options
   - TDD configuration selection

Example: 100 MHz @ n78
- Peak DL: ~1.5 Gbps (8 layers)
- Cell average: ~500-700 Mbps
- Concurrent users: ~100-200 at 10 Mbps each

[Source: Network Planning Guidelines]""",
                "category": "performance",
                "source": "Planning_Guidelines"
            },
            {
                "content": """Question: What is Self-Organizing Networks (SON) in telecom?

Answer: SON automates network configuration, optimization, and healing:

SON Categories:
1. Self-Configuration:
   - Auto-connectivity (plug-and-play)
   - Automatic parameter assignment
   - Neighbor list configuration

2. Self-Optimization:
   - Mobility Load Balancing (MLB)
   - Mobility Robustness Optimization (MRO)
   - Coverage and Capacity Optimization (CCO)
   - Energy Saving Management
   - RACH Optimization
   - Inter-Cell Interference Coordination

3. Self-Healing:
   - Cell Outage Detection (COD)
   - Cell Outage Compensation (COC)
   - Automatic fault recovery

SON Architecture:
- Centralized SON: OAM-based, slower but coordinated
- Distributed SON: eNB/gNB-based, faster response
- Hybrid SON: Combines both approaches

5G SON Enhancements:
- AI/ML-based optimization
- Intent-driven automation
- Cross-domain coordination
- Slice-aware optimization

Benefits:
- Reduced OPEX (fewer truck rolls)
- Improved network performance
- Faster problem resolution
- Better subscriber experience

[Source: 3GPP TS 32.500 - Self-Organizing Networks]""",
                "category": "network_operations",
                "source": "3GPP_TS_32.500"
            }
        ]
        
        documents = []
        for idx, item in enumerate(knowledge_base):
            doc = Document(
                content=item["content"],
                metadata={
                    "source": item["source"],
                    "category": item["category"],
                    "doc_id": f"kb_{idx}"
                }
            )
            documents.append(doc)
        
        print(f"✅ Loaded {len(documents)} documents from built-in knowledge base")
        return documents
    
    def load_pdf_documents(self, directory: str, category: str) -> List[Document]:
        """Load PDF documents from a directory using PyMuPDF."""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            print("⚠️ PyMuPDF not installed. Skipping PDF loading. Run: pip install pymupdf")
            return []

        documents = []
        pdf_dir = Path(directory)
        
        if not pdf_dir.exists():
            print(f"⚠️ Directory not found: {pdf_dir}")
            return []

        pdf_files = list(pdf_dir.glob("*.pdf"))
        print(f"📄 Found {len(pdf_files)} PDF files in {directory}")

        for pdf_file in tqdm(pdf_files, desc=f"Processing {category} PDFs"):
            try:
                doc = fitz.open(pdf_file)
                text = ""
                for page in doc:
                    text += page.get_text() + "\n"
                
                # Chunk the text
                chunks = self.chunk_text(text, source=pdf_file.name, category=category)
                documents.extend(chunks)
                
            except Exception as e:
                print(f"⚠️ Error loading {pdf_file.name}: {e}")

        return documents

    def load_all_raw_documents(self) -> List[Document]:
        """Load all documents from raw directories (Architecture Spec 3.1)."""
        all_docs = []

        # Map directories to normalized categories
        category_mapping = {
            "kpi_docs": "performance",         # -> 500 tokens
            "alarm_docs": "network_operations", # -> 250 tokens
            "config_docs": "standards",        # -> 125 tokens (config maps to standard/default)
            "maintenance_docs": "maintenance", # -> 300 tokens
            "regulatory_docs": "standards"     # -> 125 tokens
        }

        print("\n📚 Loading raw PDF documents from data/raw/...")
        
        for dir_name, category in category_mapping.items():
            dir_path = RAW_DATA_DIR / dir_name
            docs = self.load_pdf_documents(str(dir_path), category)
            all_docs.extend(docs)
            print(f"   Loaded {len(docs)} chunks for {category} from {dir_name}")

        return all_docs
    
    def load_csv_data(self, csv_dir: Optional[Path] = None) -> List[Document]:
        """Load CSV files as structured documents."""
        csv_dir = csv_dir or RAW_DATA_DIR
        documents = []
        
        try:
            import pandas as pd
            
            csv_files = list(csv_dir.glob("*.csv"))
            print(f"📊 Found {len(csv_files)} CSV files")
            
            for csv_path in tqdm(csv_files, desc="Processing CSVs"):
                try:
                    df = pd.read_csv(csv_path)
                    
                    # Convert each row to a document
                    for idx, row in df.iterrows():
                        content = "\n".join([f"{col}: {val}" for col, val in row.items()])
                        
                        doc = Document(
                            content=content,
                            metadata={
                                "source": csv_path.name,
                                "category": "network_kpi",
                                "row_index": idx
                            }
                        )
                        documents.append(doc)
                        
                except Exception as e:
                    print(f"⚠️ Error processing {csv_path.name}: {e}")
                    
            print(f"✅ Extracted {len(documents)} records from CSVs")
            
        except ImportError:
            print("⚠️ pandas not installed. Skipping CSV loading.")
            
        return documents
    
    def load_all_data(self) -> List[Document]:
        """Load all available data sources with built-in KB as supplement."""
        all_documents = []
        
        # Step 1: Try to load TeleQnA (primary source - gated)
        teleqna_docs = self.load_teleqna_dataset()
        
        # Step 2: Validate loaded data - check for empty answers
        valid_docs = []
        empty_answer_count = 0
        
        for doc in teleqna_docs:
            content = doc.content
            # Check if answer is empty or too short
            if "Answer:" in content:
                answer_part = content.split("Answer:")[-1].strip()
                if len(answer_part) < 10:  # Empty or near-empty answer
                    empty_answer_count += 1
                    continue
            valid_docs.append(doc)
        
        if empty_answer_count > 0:
            print(f"⚠️ Filtered out {empty_answer_count} documents with empty/short answers")
        
        all_documents.extend(valid_docs)
        
        # Step 3: Load 5G Fault datasets (network operations)
        print("\n📡 Loading 5G fault/troubleshooting datasets...")
        fault_full_docs = self.load_5g_faults_full_dataset()
        all_documents.extend(fault_full_docs)
        
        troubleshooting_docs = self.load_fault_troubleshooting_dataset()
        all_documents.extend(troubleshooting_docs)
        
        # Step 4: ALWAYS load built-in knowledge base as supplement
        # This ensures high-quality curated content is always available
        print("\n📚 Loading built-in knowledge base (quality supplement)...")
        builtin_docs = self.load_builtin_knowledge_base()
        all_documents.extend(builtin_docs)
        
        # Step 5: Load Raw PDFs (Architecture 3.1)
        raw_docs = self.load_all_raw_documents()
        all_documents.extend(raw_docs)
        
        # Step 6: Load CSVs if available
        csv_docs = self.load_csv_data()
        all_documents.extend(csv_docs)
        
        # Report on data quality
        categories = {}
        for doc in all_documents:
            cat = doc.metadata.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"\n📊 Data Quality Report:")
        print(f"   Total documents: {len(all_documents)}")
        print(f"   From external sources: {len(valid_docs)}")
        print(f"   From built-in KB: {len(builtin_docs)}")
        print(f"   Categories: {categories}")
        
        if len(all_documents) == 0:
            print("\n❌ CRITICAL: No documents loaded! Check data sources.")
        
        self.documents = all_documents
        return all_documents
    
    def save_processed_data(self, filename: str = "processed_documents.json"):
        """Save processed documents to JSON."""
        output_path = PROCESSED_DATA_DIR / filename
        
        data = [doc.to_dict() for doc in self.documents]
        
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
            
        print(f"💾 Saved {len(data)} documents to {output_path}")
        
    def load_processed_data(self, filename: str = "processed_documents.json") -> List[Document]:
        """Load previously processed documents."""
        input_path = PROCESSED_DATA_DIR / filename
        
        if not input_path.exists():
            print(f"⚠️ No processed data found at {input_path}")
            return []
        
        with open(input_path, "r") as f:
            data = json.load(f)
            
        self.documents = [Document.from_dict(d) for d in data]
        print(f"📂 Loaded {len(self.documents)} documents from cache")
        
        return self.documents


if __name__ == "__main__":
    # Test data loading
    loader = TelecomDataLoader()
    docs = loader.load_all_data()
    
    if docs:
        loader.save_processed_data()
        print("\n📋 Sample document:")
        print(docs[0].content[:500])
