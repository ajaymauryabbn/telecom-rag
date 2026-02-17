#!/bin/bash

# Create data directories
echo "📂 Creating data directories..."
mkdir -p data/raw/kpi_docs
mkdir -p data/raw/alarm_docs
mkdir -p data/raw/config_docs
mkdir -p data/raw/maintenance_docs
mkdir -p data/raw/regulatory_docs

# ============================================
# CATEGORY 1: KPI DEFINITIONS (Performance)
# ============================================
echo "⬇️ Downloading KPI Docs..."
cd data/raw/kpi_docs
curl -L -o 5g_ppp_kpi_whitepaper.pdf "https://5g-ppp.eu/wp-content/uploads/2022/06/white_paper_b5g-6g-kpis-camera-ready.pdf"
curl -L -o etsi_ts_128623_5g_kpi.pdf "https://www.etsi.org/deliver/etsi_ts/128600_128699/128623/17.04.02_60/ts_128623v170402p.pdf"
curl -L -o etsi_ts_128554_perf.pdf "https://www.etsi.org/deliver/etsi_ts/128500_128599/128554/16.07.00_60/ts_128554v160700p.pdf"
curl -L -o etsi_ts_128552_perf_mgmt.pdf "https://www.etsi.org/deliver/etsi_ts/128500_128599/128552/16.07.00_60/ts_128552v160700p.pdf"
cd ../../..

# ============================================
# CATEGORY 2: ALARM & TROUBLESHOOTING (Network Operations)
# ============================================
echo "⬇️ Downloading Alarm Docs..."
cd data/raw/alarm_docs
curl -L -o radcom_5g_troubleshooting.pdf "https://radcom.com/wp-content/uploads/2021/01/RADCOM-Subscriber-analytics-and-end-to-end-troubleshooting-for-5G-networks-1.pdf"
curl -L -o cambridge_ran_alarm_framework.pdf "https://www.repository.cam.ac.uk/bitstreams/6f6a7600-739c-4d1a-ad8f-df65de674177/download"
curl -L -o ran_evolution_automation.pdf "http://ir.juit.ac.in:8080/jspui/bitstream/123456789/7121/1/RAN%20Evolution%20and%20Automation.pdf"
# Note: Nokia docs require auth, skipping
cd ../../..

# ============================================
# CATEGORY 3: CONFIGURATION (Standards/Config)
# ============================================
echo "⬇️ Downloading Config Docs..."
cd data/raw/config_docs
curl -L -o huawei_5g_planning_optimization.pdf "https://www-file.huawei.com/-/media/corporate/pdf/white%20paper/2018/5g_wireless_network_planing_solution_en.pdf"
curl -L -o gti_5g_radio_intelligence.pdf "https://www.gtigroup.org/Uploads/File/2023/09/05/u64f6ec5533eb0.pdf"
curl -L -o nccs_gnodeb_config.pdf "https://nccs.gov.in/public/itsar/ITSAR303092408.pdf"
curl -L -o nccs_5g_bsf_config.pdf "https://nccs.gov.in/public/itsar/ITSAR111242311.pdf"
curl -L -o etsi_ts_138331_rrc.pdf "https://www.etsi.org/deliver/etsi_ts/138300_138399/138331/17.00.00_60/ts_138331v170000p.pdf"
cd ../../..

# ============================================
# CATEGORY 4: MAINTENANCE (Maintenance)
# ============================================
echo "⬇️ Downloading Maintenance Docs..."
cd data/raw/maintenance_docs
curl -L -o viavi_5g_maintenance.pdf "https://www.viavisolutions.com/en-us/literature/5g-network-installation-maintenance-solutions-brochures-en.pdf"
curl -L -o motorola_preventive_maintenance.pdf "https://www.motorolasolutions.com/content/dam/msi/docs/federal_standards_terms_and_conditions/preventive_maintenance_sow.pdf"
curl -L -o att_cell_site_requirements.pdf "https://www.business.att.com/content/dam/attbusiness/prime-access/customer-requirements-at-cell-sites.pdf"
curl -L -o tia_222_tower_maintenance.pdf "https://tifonline.org/wp-content/uploads/2022/08/PAN-ANSI-TIA-222.pdf"
curl -L -o telecom_room_checklist.pdf "https://facilities.follettsoftware.com/wp-content/uploads/2024/04/TR-Design-Build-Checklist-24Q2.pdf"
curl -L -o tower_maintenance_standards.pdf "https://www.nqr.gov.in/qualification/file/QF_Telecom%20Tower%20Site%20Maintenance%20Technician.pdf"
curl -L -o cell_tower_inspection.pdf "https://www.fulcrumapp.com/wp-content/uploads/resources/5ff75ab7d054f136dba668f9_Fulcrum20Checklist_Cell_Telecom20Tower20Inspect.pdf"
cd ../../..

# ============================================
# CATEGORY 5: REGULATORY (Standards)
# ============================================
echo "⬇️ Downloading Regulatory Docs..."
cd data/raw/regulatory_docs
curl -L -o tec_5g_security.pdf "https://www.tec.gov.in/pdf/Studypaper/Study%20Paper%20on%205G%20Security%20_final.pdf"
curl -L -o tec_ran_optimization.pdf "https://www.tec.gov.in/public/pdf/GR3/TEC-GR-SS-RAN-001-01-MAR-14.pdf"
curl -L -o ibm_netcool_nokia_probe.pdf "https://www.ibm.com/docs/SSSHTQ/nkna3cov6-pdf.pdf"
curl -L -o airtel_trai_interconnection.pdf "https://www.trai.gov.in/sites/default/files/2025-12/BAL_16122025.pdf"
curl -L -o airtel_consumer_charter.pdf "https://assets.airtel.in/static-assets/cms/Airtel_Telecom_Consumers_Charter_English_2025.pdf"
cd ../../..

echo "✅ Download complete!"
