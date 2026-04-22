"""
core/mbr_parser.py
==================
This module provides functions to parse and validate Master Boot Record (MBR) data.
"""

import struct

MBR_SIZE = 512
BOOT_CODE_SIZE = 440
PARTITION_TABLE_OFFSET = 446
PARTITION_ENTRY_SIZE = 16
BOOT_SIGNATURE = b'\x55\xAA'


# ─────────────────────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────────────────────

def validate_mbr(mbr_bytes: bytes):
    """
    Ensure the provided data is exactly 512 bytes.
    """
    if not isinstance(mbr_bytes, bytes):
        raise TypeError("MBR data must be of type 'bytes'.")
    if len(mbr_bytes) != MBR_SIZE:
        raise ValueError("Invalid MBR size. Expected exactly 512 bytes.")
    else:
        print("MBR validation successful: Correct size (512 bytes)!")


# ─────────────────────────────────────────────────────────────
# BOOT CODE
# ─────────────────────────────────────────────────────────────

def extract_boot_code(mbr_bytes: bytes) -> bytes:
    """
    Extract the first 440 bytes of boot code from the MBR.
    """
    validate_mbr(mbr_bytes)
    return mbr_bytes[:BOOT_CODE_SIZE] # extracting the first 440 bytes of boot code from the MBR


# ─────────────────────────────────────────────────────────────
# DISK SIGNATURE
# ─────────────────────────────────────────────────────────────

def extract_disk_signature(mbr_bytes: bytes) -> str:
    """
    Extract 4-byte disk signature (bytes 440–443).
    Returns hex string representation.
    """
    validate_mbr(mbr_bytes)
    signature = mbr_bytes[440:444] 
    return signature.hex()


# ─────────────────────────────────────────────────────────────
# BOOT SIGNATURE CHECK
# ─────────────────────────────────────────────────────────────

def validate_boot_signature(mbr_bytes: bytes) -> bool:
    """
    Verify that the last two bytes are 0x55AA.
    """
    validate_mbr(mbr_bytes)
    return mbr_bytes[510:512] == BOOT_SIGNATURE


# ─────────────────────────────────────────────────────────────
# PARTITION TABLE PARSING
# ─────────────────────────────────────────────────────────────

def parse_partition_table(mbr_bytes: bytes) -> list:  # list stores the parsed partition entries as dictionaries
    """
    Parse the 4 partition entries from the MBR.
    Returns:
        List of dictionaries:
        [
            {
                "boot_flag": int,            -> 1 = bootable, 0 = not bootable
                "partition_type": int,       -> e.g., 0x07 for NTFS, 0x83 for Linux
                "start_lba": int,            -> Starting sector (LBA)
                "size_in_sectors": int       -> Size of the partition in sectors
            },
            ...
        ]
    """
    validate_mbr(mbr_bytes)

    partitions = []
    offset = PARTITION_TABLE_OFFSET

    for i in range(4):
        entry = mbr_bytes[offset:offset + PARTITION_ENTRY_SIZE]

        boot_flag = entry[0]
        partition_type = entry[4]

        start_lba = struct.unpack("<I", entry[8:12])[0]
        size_in_sectors = struct.unpack("<I", entry[12:16])[0]

        partitions.append({
            "boot_flag": boot_flag,
            "partition_type": partition_type,
            "start_lba": start_lba,
            "size_in_sectors": size_in_sectors
        })

        offset += PARTITION_ENTRY_SIZE

    #printing for time being to check if values are being parsed correctly
    # for idx, part in enumerate(partitions):
    #     print(f"Partition {idx + 1}:")
    #     print(f"  Boot Flag: {part['boot_flag']:#04x} ({'Bootable' if part['boot_flag'] == 0x80 else 'Non-bootable'})")
    #     print(f"  Partition Type: {part['partition_type']:#04x}")
    #     print(f"  Start LBA: {part['start_lba']}")
    #     print(f"  Size in Sectors: {part['size_in_sectors']}")
    return partitions 