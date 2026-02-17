# Data Acquisition Plan for Telecom RAG

## Current Status
- **Total Documents**: 12,500
- **Coverage**: 85% of architecture requirements
- **Missing**: ~1,000 more docs needed for full operational coverage

---

## STEP 1: Download Documents from Repository File

### Source File
`# Telecom RAG System - Document Reposito.md` (already in project root)

### Download Commands

```bash
# Create download directory
mkdir -p data/raw/kpi_docs
mkdir -p data/raw/alarm_docs
mkdir -p data/raw/config_docs
mkdir -p data/raw/maintenance_docs
mkdir -p data/raw/regulatory_docs

# ============================================
# CATEGORY 1: KPI DEFINITIONS (4 docs)
# ============================================
cd data/raw/kpi_docs

# 5G PPP KPI Whitepaper
wget -O 5g_ppp_kpi_whitepaper.pdf "https://5g-ppp.eu/wp-content/uploads/2022/06/white_paper_b5g-6g-kpis-camera-ready.pdf"

# ETSI TS 128 623 - 5G KPI Standards
wget -O etsi_ts_128623_5g_kpi.pdf "https://www.etsi.org/deliver/etsi_ts/128600_128699/128623/17.04.02_60/ts_128623v170402p.pdf"

# ETSI TS 128 554 - Performance Measurements
wget -O etsi_ts_128554_perf.pdf "https://www.etsi.org/deliver/etsi_ts/128500_128599/128554/16.07.00_60/ts_128554v160700p.pdf"

# 3GPP TS 32.425 (DOC format - may need manual download)
# URL: https://www.3gpp.org/ftp/tsg_sa/wg5_tm/TSGS5_110/SA_input/specs_review/32425-e10.doc

# ============================================
# CATEGORY 2: ALARM & TROUBLESHOOTING (6 docs)
# ============================================
cd ../alarm_docs

# RADCOM 5G Troubleshooting
wget -O radcom_5g_troubleshooting.pdf "https://radcom.com/wp-content/uploads/2021/01/RADCOM-Subscriber-analytics-and-end-to-end-troubleshooting-for-5G-networks-1.pdf"

# Cambridge RAN Alarm Framework
wget -O cambridge_ran_alarm_framework.pdf "https://www.repository.cam.ac.uk/bitstreams/6f6a7600-739c-4d1a-ad8f-df65de674177/download"

# RAN Evolution & Automation
wget -O ran_evolution_automation.pdf "http://ir.juit.ac.in:8080/jspui/bitstream/123456789/7121/1/RAN%20Evolution%20and%20Automation.pdf"

# Nokia docs (may require auth - try these):
# https://documentation.nokia.com/cgi-bin/dbaccessfilename.cgi/3HE18165AAAATQZZA_V1_NSP%2022.3%20Simplified%20RAN%20Transport%20Solution%20-%20NSP%20Network%20Services%20Platform%20-%20Release%2022.3.pdf
# https://documentation.nokia.com/cgi-bin/dbaccessfilename.cgi/3HE18125AAAATQZZA_V1_NSP%2022.3%20Fault%20Management%20Application%20Help%20-%20NSP%20Network%20Services%20Platform%20-%20Release%2022.3.pdf

# ============================================
# CATEGORY 3: CONFIGURATION & PARAMETERS (6 docs)
# ============================================
cd ../config_docs

# Huawei 5G Network Planning
wget -O huawei_5g_planning_optimization.pdf "https://www-file.huawei.com/-/media/corporate/pdf/white%20paper/2018/5g_wireless_network_planing_solution_en.pdf"

# GTI 5G Radio Network Intelligence
wget -O gti_5g_radio_intelligence.pdf "https://www.gtigroup.org/Uploads/File/2023/09/05/u64f6ec5533eb0.pdf"

# NCCS 5G gNodeB Configuration
wget -O nccs_gnodeb_config.pdf "https://nccs.gov.in/public/itsar/ITSAR303092408.pdf"

# NCCS 5G BSF Configuration
wget -O nccs_5g_bsf_config.pdf "https://nccs.gov.in/public/itsar/ITSAR111242311.pdf"

# 3GPP 38.331 RRC (reference page - specs need manual download)
# URL: https://www.3gpp.org/dynareport/38331.htm

# ============================================
# CATEGORY 4: MAINTENANCE & OPERATIONS (8 docs)
# ============================================
cd ../maintenance_docs

# Viavi 5G Installation & Maintenance
wget -O viavi_5g_maintenance.pdf "https://www.viavisolutions.com/en-us/literature/5g-network-installation-maintenance-solutions-brochures-en.pdf"

# Motorola Preventive Maintenance SOP
wget -O motorola_preventive_maintenance.pdf "https://www.motorolasolutions.com/content/dam/msi/docs/federal_standards_terms_and_conditions/preventive_maintenance_sow.pdf"

# AT&T Cell Site Requirements
wget -O att_cell_site_requirements.pdf "https://www.business.att.com/content/dam/attbusiness/prime-access/customer-requirements-at-cell-sites.pdf"

# TIA-222 Tower Maintenance Standard
wget -O tia_222_tower_maintenance.pdf "https://tifonline.org/wp-content/uploads/2022/08/PAN-ANSI-TIA-222.pdf"

# Telecom Room Design Checklist
wget -O telecom_room_checklist.pdf "https://facilities.follettsoftware.com/wp-content/uploads/2024/04/TR-Design-Build-Checklist-24Q2.pdf"

# Tower Maintenance Technician Standards
wget -O tower_maintenance_standards.pdf "https://www.nqr.gov.in/qualification/file/QF_Telecom%20Tower%20Site%20Maintenance%20Technician.pdf"

# Cell Tower Inspection Checklist
wget -O cell_tower_inspection.pdf "https://www.fulcrumapp.com/wp-content/uploads/resources/5ff75ab7d054f136dba668f9_Fulcrum20Checklist_Cell_Telecom20Tower20Inspect.pdf"

# ============================================
# CATEGORY 5: REGULATORY & ADDITIONAL (5 docs)
# ============================================
cd ../regulatory_docs

# TEC India 5G Security
wget -O tec_5g_security.pdf "https://www.tec.gov.in/pdf/Studypaper/Study%20Paper%20on%205G%20Security%20_final.pdf"

# TEC RAN Optimization Guidelines
wget -O tec_ran_optimization.pdf "https://www.tec.gov.in/public/pdf/GR3/TEC-GR-SS-RAN-001-01-MAR-14.pdf"

# IBM Netcool Nokia-Siemens Probe
wget -O ibm_netcool_nokia_probe.pdf "https://www.ibm.com/docs/SSSHTQ/nkna3cov6-pdf.pdf"

# Airtel TRAI Submissions (from existing guide)
wget -O airtel_trai_interconnection.pdf "https://www.trai.gov.in/sites/default/files/2025-12/BAL_16122025.pdf"
wget -O airtel_consumer_charter.pdf "https://assets.airtel.in/static-assets/cms/Airtel_Telecom_Consumers_Charter_English_2025.pdf"

cd ../../..
```

---

## STEP 2: Directory Structure

After downloading, your `data/raw/` should look like:

```
data/raw/
├── kpi_docs/
│   ├── 5g_ppp_kpi_whitepaper.pdf
│   ├── etsi_ts_128623_5g_kpi.pdf
│   ├── etsi_ts_128554_perf.pdf
│   └── 3gpp_ts_32425.doc (manual)
├── alarm_docs/
│   ├── radcom_5g_troubleshooting.pdf
│   ├── cambridge_ran_alarm_framework.pdf
│   ├── ran_evolution_automation.pdf
│   └── nokia_*.pdf (if accessible)
├── config_docs/
│   ├── huawei_5g_planning_optimization.pdf
│   ├── gti_5g_radio_intelligence.pdf
│   ├── nccs_gnodeb_config.pdf
│   └── nccs_5g_bsf_config.pdf
├── maintenance_docs/
│   ├── viavi_5g_maintenance.pdf
│   ├── motorola_preventive_maintenance.pdf
│   ├── att_cell_site_requirements.pdf
│   ├── tia_222_tower_maintenance.pdf
│   ├── telecom_room_checklist.pdf
│   ├── tower_maintenance_standards.pdf
│   └── cell_tower_inspection.pdf
└── regulatory_docs/
    ├── tec_5g_security.pdf
    ├── tec_ran_optimization.pdf
    ├── ibm_netcool_nokia_probe.pdf
    ├── airtel_trai_interconnection.pdf
    └── airtel_consumer_charter.pdf
```

---

## STEP 3: Update Data Loader

Modify `src/data_loader.py` to load PDFs from these new directories:

```python
# Add PDF loading capability
def load_pdf_documents(self, directory: str, category: str) -> List[Document]:
    """Load PDF documents from a directory."""
    import fitz  # PyMuPDF

    documents = []
    pdf_dir = Path(directory)

    for pdf_file in pdf_dir.glob("*.pdf"):
        try:
            doc = fitz.open(pdf_file)
            text = ""
            for page in doc:
                text += page.get_text()

            # Chunk the text
            chunks = self.chunk_text(text, source=pdf_file.stem, category=category)
            documents.extend(chunks)
            print(f"  Loaded {len(chunks)} chunks from {pdf_file.name}")
        except Exception as e:
            print(f"  Error loading {pdf_file.name}: {e}")

    return documents

def load_all_raw_documents(self) -> List[Document]:
    """Load all documents from raw directories."""
    all_docs = []

    category_mapping = {
        "kpi_docs": "performance",
        "alarm_docs": "troubleshooting",
        "config_docs": "configuration",
        "maintenance_docs": "maintenance",
        "regulatory_docs": "regulatory"
    }

    for dir_name, category in category_mapping.items():
        dir_path = RAW_DATA_DIR / dir_name
        if dir_path.exists():
            print(f"Loading {dir_name}...")
            docs = self.load_pdf_documents(str(dir_path), category)
            all_docs.extend(docs)

    return all_docs
```

---

## STEP 4: Add PyMuPDF Dependency

```bash
pip install pymupdf
```

Or add to `requirements.txt`:
```
pymupdf>=1.23.0
```

---

## STEP 5: Re-ingest Data

After downloading and updating the loader:

```bash
# Clear old cache (optional - if you want fresh start)
rm -f data/bm25_index.pkl

# Run ingestion
python -c "
from src.data_loader import TelecomDataLoader
from src.vector_store import TelecomVectorStore

loader = TelecomDataLoader()
docs = loader.load_all_raw_documents()
print(f'Loaded {len(docs)} new documents')

store = TelecomVectorStore()
store.add_documents(docs)
print('Ingestion complete!')
"
```

---

## Expected Results After Completion

| Category | Before | After | Target |
|----------|--------|-------|--------|
| KPIs/Performance | 22 | ~200+ | 200 |
| Alarms/Troubleshooting | 2,466 | ~2,600+ | 3,000 |
| Configuration | 0 | ~150+ | 150 |
| Maintenance | 1 | ~100+ | 100 |
| Regulatory | 6 | ~15+ | 10 |
| **TOTAL** | 12,500 | **~13,500+** | 13,500 |

---

## Priority Download Order

If time is limited, download in this order:

### P1 - Critical (Do First)
1. `etsi_ts_128623_5g_kpi.pdf` - KPI definitions
2. `huawei_5g_planning_optimization.pdf` - Config parameters
3. `radcom_5g_troubleshooting.pdf` - Troubleshooting guide
4. `viavi_5g_maintenance.pdf` - Maintenance procedures

### P2 - Important (Do Second)
5. `5g_ppp_kpi_whitepaper.pdf`
6. `nccs_gnodeb_config.pdf`
7. `motorola_preventive_maintenance.pdf`
8. `att_cell_site_requirements.pdf`

### P3 - Nice to Have (Do Last)
9. All remaining PDFs from the list

---

## Notes for Antigravity

1. **Some URLs may require authentication** (Nokia docs especially) - skip if blocked
2. **3GPP specs** are at index pages - may need to navigate to download actual PDFs
3. **Chunking**: Use category-specific chunk sizes per architecture:
   - Performance: 500 tokens
   - Alarms: 250 tokens
   - Config/Standards: 125 tokens
   - Maintenance: 300 tokens
4. **After ingestion**, delete `data/bm25_index.pkl` to force BM25 rebuild

---

**Document Created**: January 30, 2026
**Target Completion**: ~29 new PDF documents = ~1,000 additional chunks
