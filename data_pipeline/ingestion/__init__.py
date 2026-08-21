"""
Phase 3: Data Ingestion & Raw Parsing Layer.
Provides format detection, CMLRE TXT/CSV parsing, schema normalization,
and canonical file exportation.
"""

from data_pipeline.ingestion.canonical_exporter import (
    export_canonical_csv,
    export_canonical_xlsx,
)
from data_pipeline.ingestion.format_detector import (
    classify_domain,
    detect_format_and_preview,
)
from data_pipeline.ingestion.ingestion_manager import process_upload
from data_pipeline.ingestion.process_dataset import process_all_datasets
from data_pipeline.ingestion.schema_normalizer import (
    CANONICAL_COLUMN_MAPPINGS,
    normalize_dataframe_columns,
)
from data_pipeline.ingestion.txt_parser import (
    detect_delimiter_and_header,
    extract_preamble_metadata,
    parse_cmlre_txt,
)

__all__ = [
    "classify_domain",
    "detect_format_and_preview",
    "detect_delimiter_and_header",
    "extract_preamble_metadata",
    "parse_cmlre_txt",
    "normalize_dataframe_columns",
    "CANONICAL_COLUMN_MAPPINGS",
    "export_canonical_csv",
    "export_canonical_xlsx",
    "process_upload",
    "process_all_datasets",
]
