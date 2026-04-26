# Data

Raw and processed data files are **not committed to this repo**. They live in Google Drive for Colab compatibility and to keep the repo size small.

## Directory structure (in Google Drive)

MyDrive/
└── fincrime-sentinel-data/
├── raw/
│   ├── HI-Small_Trans.csv
│   └── HI-Small_Patterns.txt
├── processed/
│   └── transactions.parquet
├── typology_guidance/
│   └── (AUSTRAC PDFs)
└── sanctions/
└── (DFAT consolidated list)

## Data sources

### Primary — IBM AML HI-Small (synthetic)
- Kaggle: https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml
- License: CDLA-Sharing-1.0
- Paper: https://arxiv.org/abs/2306.16424

### Regulatory context (real, public)
- AUSTRAC Banking Sector Indicators: https://www.austrac.gov.au/business/how-comply-guidance-and-resources/guidance-resources/indicators-suspicious-activity-banking-sector-0
- AUSTRAC SMR Reference Guide: https://www.austrac.gov.au/sites/default/files/2021-04/AUSTRAC_suspicious%20matter%20reporting_reference%20guide.pdf
- DFAT Consolidated Sanctions List: https://www.dfat.gov.au/international-relations/security/sanctions/consolidated-list
EOF
