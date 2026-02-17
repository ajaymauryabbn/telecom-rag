# Manual Download Instructions 📥

Some critical documents could not be downloaded automatically due to authentication requirements. Please download the following 2 files manually and place them in the specified directories.

## 1. Nokia NSP Simplified RAN Transport
- **Description**: Transport solution guide for 5G.
- **Requirement**: Nokia Support Portal Account.
- **Download Link**: [Nokia NSP 22.3 Guide](https://documentation.nokia.com/cgi-bin/dbaccessfilename.cgi/3HE18165AAAATQZZA_V1_NSP%2022.3%20Simplified%20RAN%20Transport%20Solution%20-%20NSP%20Network%20Services%20Platform%20-%20Release%2022.3.pdf)
- **Target Path**: `data/raw/alarm_docs/nokia_nsp_transport.pdf`

## 2. Nokia NSP Fault Management
- **Description**: Fault management application help.
- **Requirement**: Nokia Support Portal Account.
- **Download Link**: [Nokia FM App Help](https://documentation.nokia.com/cgi-bin/dbaccessfilename.cgi/3HE18125AAAATQZZA_V1_NSP%2022.3%20Fault%20Management%20Application%20Help%20-%20NSP%20Network%20Services%20Platform%20-%20Release%2022.3.pdf)
- **Target Path**: `data/raw/alarm_docs/nokia_nsp_fault_mgmt.pdf`

---

## After Downloading
Once you have placed these files in the `data/raw/` subdirectories, run the ingestion command to load them:

```bash
python3 -c "from src.retriever import TelecomRetriever; Retriever = TelecomRetriever(auto_init=False); Retriever.ingest_data(force_reload=True)"
```
