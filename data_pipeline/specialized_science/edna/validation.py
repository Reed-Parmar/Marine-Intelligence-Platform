"""
Phase 7 — eDNA Sequence Validation (FASTA and FASTQ).
Validates file structure, header syntax, nucleotide characters, and Phred quality strings.
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple, Union


# Standard IUPAC nucleotide characters (DNA + RNA + ambiguous codes + gap)
VALID_NUCLEOTIDES = set("ACGTUNRYSWKMBDHV-.")


@dataclass
class FASTARecord:
    """Parsed single FASTA entry."""
    header: str
    sequence: str
    line_number: int
    id: str = ""
    description: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.id:
            parts = self.header.split(None, 1)
            self.id = parts[0] if parts else ""
            self.description = parts[1] if len(parts) > 1 else None


@dataclass
class FASTQRecord:
    """Parsed single 4-line FASTQ entry."""
    header: str
    sequence: str
    quality: str
    line_number: int
    id: str = ""
    description: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.id:
            parts = self.header.split(None, 1)
            self.id = parts[0] if parts else ""
            self.description = parts[1] if len(parts) > 1 else None


@dataclass
class EDNAValidationResult:
    """Structured result returned by eDNA sequence validators."""
    is_valid: bool
    format: str # 'fasta', 'fastq', 'raw_sequence'
    total_records: int
    valid_records_count: int
    invalid_records_count: int
    fasta_records: List[FASTARecord] = field(default_factory=list)
    fastq_records: List[FASTQRecord] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "format": self.format,
            "total_records": self.total_records,
            "valid_records_count": self.valid_records_count,
            "invalid_records_count": self.invalid_records_count,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def validate_sequence_string(seq: str) -> Tuple[bool, List[str]]:
    """Validates raw sequence string for valid IUPAC nucleotide characters."""
    if not seq or not seq.strip():
        return False, ["Sequence is empty."]

    cleaned = seq.strip().upper().replace(" ", "").replace("\n", "").replace("\r", "")
    invalid_chars = set(cleaned) - VALID_NUCLEOTIDES
    if invalid_chars:
        return False, [f"Sequence contains invalid nucleotide characters: {sorted(invalid_chars)}"]

    return True, []


def _read_content(content_or_path: Union[str, Path]) -> List[str]:
    """Reads lines from either a file path or raw string content."""
    if isinstance(content_or_path, Path):
        with open(content_or_path, "r", encoding="utf-8", errors="replace") as f:
            return f.readlines()
    if isinstance(content_or_path, str):
        if not ("\n" in content_or_path or content_or_path.startswith(("> ", ">", "@"))) and os.path.isfile(content_or_path):
            with open(content_or_path, "r", encoding="utf-8", errors="replace") as f:
                return f.readlines()
        return content_or_path.splitlines(keepends=True)
    return str(content_or_path).splitlines(keepends=True)


def validate_fasta(content_or_path: Union[str, Path]) -> EDNAValidationResult:
    """
    Validates FASTA format data. Supports multi-line sequence wrapping.
    """
    lines = _read_content(content_or_path)
    errors: List[str] = []
    warnings: List[str] = []
    records: List[FASTARecord] = []
    invalid_records_count = 0

    if not lines or not any(l.strip() for l in lines):
        return EDNAValidationResult(
            is_valid=False,
            format="fasta",
            total_records=0,
            valid_records_count=0,
            invalid_records_count=0,
            errors=["FASTA file is completely empty."],
        )

    current_header = None
    current_seq_lines: List[str] = []
    record_start_line = 0

    for idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith(">"):
            if current_header is not None:
                full_seq = "".join(current_seq_lines)
                is_valid_seq, seq_errs = validate_sequence_string(full_seq)
                if is_valid_seq:
                    records.append(FASTARecord(header=current_header, sequence=full_seq, line_number=record_start_line))
                else:
                    invalid_records_count += 1
                    errors.append(f"Record at line {record_start_line} (>{current_header}): {'; '.join(seq_errs)}")

            current_header = line[1:].strip()
            current_seq_lines = []
            record_start_line = idx
        else:
            if current_header is None:
                errors.append(f"Line {idx}: Sequence content found before any FASTA '>' header.")
                break
            current_seq_lines.append(line)

    # Final record
    if current_header is not None:
        full_seq = "".join(current_seq_lines)
        is_valid_seq, seq_errs = validate_sequence_string(full_seq)
        if is_valid_seq:
            records.append(FASTARecord(header=current_header, sequence=full_seq, line_number=record_start_line))
        else:
            invalid_records_count += 1
            errors.append(f"Record at line {record_start_line} (>{current_header}): {'; '.join(seq_errs)}")

    total_records = len(records) + invalid_records_count
    is_valid = len(errors) == 0 and len(records) > 0

    return EDNAValidationResult(
        is_valid=is_valid,
        format="fasta",
        total_records=total_records,
        valid_records_count=len(records),
        invalid_records_count=invalid_records_count,
        fasta_records=records,
        errors=errors,
        warnings=warnings,
    )


def validate_fastq(content_or_path: Union[str, Path]) -> EDNAValidationResult:
    """
    Validates 4-line FASTQ format entries:
    Line 1: @<header>
    Line 2: <sequence>
    Line 3: +[optional header repeat]
    Line 4: <quality string matching sequence length>
    """
    lines = _read_content(content_or_path)
    errors: List[str] = []
    warnings: List[str] = []
    records: List[FASTQRecord] = []

    non_empty = [(i, l.rstrip("\r\n")) for i, l in enumerate(lines, start=1) if l.strip()]
    if not non_empty:
        return EDNAValidationResult(
            is_valid=False,
            format="fastq",
            total_records=0,
            valid_records_count=0,
            invalid_records_count=0,
            errors=["FASTQ content is empty."],
        )

    if len(non_empty) % 4 != 0:
        errors.append(f"FASTQ record count mismatch: Expected multiple of 4 lines, found {len(non_empty)} lines.")

    num_records = len(non_empty) // 4
    for r_idx in range(num_records):
        base = r_idx * 4
        h_line_no, h_line = non_empty[base]
        s_line_no, s_line = non_empty[base + 1]
        p_line_no, p_line = non_empty[base + 2]
        q_line_no, q_line = non_empty[base + 3]

        if not h_line.startswith("@"):
            errors.append(f"Line {h_line_no}: FASTQ header must start with '@', found '{h_line[:10]}'")
            continue

        if not p_line.startswith("+"):
            errors.append(f"Line {p_line_no}: FASTQ separator line must start with '+', found '{p_line[:10]}'")
            continue

        seq_clean = s_line.strip().upper()
        is_seq_valid, seq_errs = validate_sequence_string(seq_clean)
        if not is_seq_valid:
            errors.append(f"Line {s_line_no}: Sequence validation error: {'; '.join(seq_errs)}")
            continue

        if len(seq_clean) != len(q_line):
            errors.append(
                f"Line {q_line_no}: Quality score length ({len(q_line)}) does not match sequence length ({len(seq_clean)})"
            )
            continue

        # Check Phred quality ASCII characters (Standard Sanger / Illumina 1.8+ Phred+33: 33-126)
        invalid_qual = [c for c in q_line if ord(c) < 33 or ord(c) > 126]
        if invalid_qual:
            errors.append(f"Line {q_line_no}: Invalid ASCII Phred quality characters detected.")
            continue

        records.append(
            FASTQRecord(
                header=h_line[1:].strip(),
                sequence=seq_clean,
                quality=q_line,
                line_number=h_line_no,
            )
        )

    is_valid = len(errors) == 0 and len(records) > 0

    return EDNAValidationResult(
        is_valid=is_valid,
        format="fastq",
        total_records=num_records,
        valid_records_count=len(records),
        invalid_records_count=num_records - len(records),
        fastq_records=records,
        errors=errors,
        warnings=warnings,
    )
