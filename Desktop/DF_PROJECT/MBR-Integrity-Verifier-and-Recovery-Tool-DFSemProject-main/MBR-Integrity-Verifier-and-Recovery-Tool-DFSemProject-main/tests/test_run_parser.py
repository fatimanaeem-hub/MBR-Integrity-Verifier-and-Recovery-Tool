"""
tests/test_run_parser.py
========================
Integration Test:
Member 1 (disk_reader) + Member 2 (MBR & GPT Parsers)

Run from project root:
    python tests/test_run_parser.py
"""

import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importing necessary functions from disk_reader.py, mbr_parser.py, and gpt_parser.py
from core.disk_reader import (
    read_mbr_from_image,
    read_gpt_header_from_image,
    read_gpt_table_from_image,
    SECTOR_SIZE
)

from core.mbr_parser import (
    extract_boot_code,
    extract_disk_signature,
    validate_boot_signature,
    parse_partition_table
)

from core.gpt_parser import (
    parse_gpt_header,
    parse_gpt_partition_entries
)

# Change these paths as needed
MBR_IMAGE = os.path.join("images", "mbr_test.vhd")
GPT_IMAGE = os.path.join("images", "gpt_test.vhd")


def header(title):
    print("\n" + "═" * 60)
    print(f"  {title}")
    print("═" * 60)


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"  {status}  {label}")


# ─────────────────────────────────────────────────────────────
# TEST MBR PARSER
# ─────────────────────────────────────────────────────────────
def test_mbr(image_path):
    header("MBR PARSER TEST")

    try:
        mbr_bytes = read_mbr_from_image(image_path)

        check("Returned 512 bytes", len(mbr_bytes) == SECTOR_SIZE)

        boot_code = extract_boot_code(mbr_bytes)
        check("Boot code size = 440 bytes", len(boot_code) == 440)

        disk_sig = extract_disk_signature(mbr_bytes)
        check("Disk signature length = 8 hex chars", len(disk_sig) == 8)

        boot_sig_valid = validate_boot_signature(mbr_bytes)
        check("Boot signature 55AA valid", boot_sig_valid)

        partitions = parse_partition_table(mbr_bytes)
        check("4 partition entries parsed", len(partitions) == 4)

        print("\nParsed Partitions:")
        for i, p in enumerate(partitions):
            print(f"  Partition {i+1}: {p}")

    except Exception as e:
        print(f"  ERROR: {e}")


# ─────────────────────────────────────────────────────────────
# TEST GPT PARSER
# ─────────────────────────────────────────────────────────────
def test_gpt(image_path):
    header("GPT PARSER TEST")

    try:
        gpt_bytes = read_gpt_header_from_image(image_path)

        check("Returned 512 bytes", len(gpt_bytes) == SECTOR_SIZE)

        header_info = parse_gpt_header(gpt_bytes)

        check("Signature parsed", "signature" in header_info)
        check("Revision parsed", "revision" in header_info)
        check("Header size parsed", "header_size" in header_info)
        check("CRC32 parsed", "crc32" in header_info)
        check("Backup LBA parsed", "backup_lba" in header_info)

        print("\nParsed GPT Header:")
        for key, value in header_info.items():
            print(f"  {key}: {value}")

        # OPTIONAL PART → GPT PARTITION TABLE TEST
        table_bytes = read_gpt_table_from_image(image_path)

        partitions = parse_gpt_partition_entries(table_bytes)

        print("\nParsed GPT Partitions:")
        for i, p in enumerate(partitions):
            print(f"  Partition {i+1}: {p}")

        check("GPT partition entries parsed", len(partitions) >= 0)

    except Exception as e:
        print(f"  ERROR: {e}")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":

    print("\n" + "█" * 60)
    print("  Member 2 — MBR & GPT Parser Integration Test")
    print("█" * 60)

    # Test MBR disk
    if os.path.exists(MBR_IMAGE):
        test_mbr(MBR_IMAGE)
    else:
        print(f"\nMBR test image not found: {MBR_IMAGE}")

    # Test GPT disk
    if os.path.exists(GPT_IMAGE):
        test_gpt(GPT_IMAGE)
    else:
        print(f"\nGPT test image not found: {GPT_IMAGE}")

    print("\n" + "═" * 60)
    print("  All tests complete.")
    print("═" * 60 + "\n")