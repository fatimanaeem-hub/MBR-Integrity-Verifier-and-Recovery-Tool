"""
core/gpt_parser.py
==================
GPT Header Parsing Module
Parses the Primary or Backup GPT Header sector.
"""

import struct

MIN_GPT_HEADER_SIZE = 92
GPT_SIGNATURE = b"EFI PART"
GPT_ENTRY_SIZE = 128
GPT_PARTITION_ARRAY_START = 512  # LBA 2 starts after header (512 bytes)


# ─────────────────────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────────────────────

def validate_gpt_header(header_bytes: bytes): # checks if header is at least 92 bytes long and is of type bytes
    """
    Ensure header contains at least required 92 bytes.
    """
    if not isinstance(header_bytes, bytes):
        raise TypeError("GPT header must be of type 'bytes'.")
    if len(header_bytes) < MIN_GPT_HEADER_SIZE:
        raise ValueError("Invalid GPT header size. Must be at least 92 bytes.")
    else:
        print("GPT header validation successful: Correct size (at least 92 bytes)!")

# ─────────────────────────────────────────────────────────────
# GPT HEADER PARSER
# ─────────────────────────────────────────────────────────────

def parse_gpt_header(header_bytes: bytes) -> dict: # dict will store the parsed fieldsfrom header
    """
    Parse GPT header fields and return structured dictionary.
    """
    validate_gpt_header(header_bytes)

    signature = header_bytes[0:8]                                   # first 8 bytes for signature, should be "EFI PART"
    revision = struct.unpack("<I", header_bytes[8:12])[0]           # next 4 bytes for revision, little-endian unsigned int
    header_size = struct.unpack("<I", header_bytes[12:16])[0]       # next 4 bytes for header size, little-endian unsigned int
    crc32 = struct.unpack("<I", header_bytes[16:20])[0]             # next 4 bytes for CRC32 checksum, little-endian unsigned int
    current_lba = struct.unpack("<Q", header_bytes[24:32])[0]       # bytes 24-31 for current LBA, little-endian unsigned long long
    backup_lba = struct.unpack("<Q", header_bytes[32:40])[0]        # bytes 32-39 for backup LBA, little-endian unsigned long long
    first_usable_lba = struct.unpack("<Q", header_bytes[40:48])[0]  # bytes 40-47 for first usable LBA, little-endian unsigned long long
    last_usable_lba = struct.unpack("<Q", header_bytes[48:56])[0]   # bytes 48-55 for last usable LBA, little-endian unsigned long long

    # printing for time being to check if values are being parsed correctly
    # print(f"GPT Signature: {signature}")
    # print(f"Revision: {revision}") 
    # print(f"Header Size: {header_size} bytes")
    # print(f"CRC32 Checksum: {crc32:#010x}")
    # print(f"Current LBA: {current_lba}")
    # print(f"Backup LBA: {backup_lba}")
    # print(f"First Usable LBA: {first_usable_lba}")
    # print(f"Last Usable LBA: {last_usable_lba}")

    return {
        "signature": signature.decode(errors="ignore"),
        "revision": revision,
        "header_size": header_size,
        "crc32": crc32,
        "current_lba": current_lba,
        "backup_lba": backup_lba,
        "first_usable_lba": first_usable_lba,
        "last_usable_lba": last_usable_lba,
        "is_valid_signature": signature == GPT_SIGNATURE
    }

# this return dict will be used to validate the signature and check if it matches "EFI PART" to confirm it's a valid GPT header.

# ─────────────────────────────────────────────────────────────
# GPT PARTITION TABLE PARSER (for optional part)
# ─────────────────────────────────────────────────────────────

def parse_gpt_partition_entries(gpt_table_bytes: bytes, max_entries: int = 4) -> list:
    """
    Parse GPT partition entries from raw GPT partition table region.
    Returns structured list of partition metadata.
    """

    if not isinstance(gpt_table_bytes, bytes):
        raise TypeError("GPT partition table must be bytes.")

    partitions = [] # list to store the parsed partition entries as dictionaries

    for i in range(max_entries):
        offset = i * GPT_ENTRY_SIZE
        entry = gpt_table_bytes[offset:offset + GPT_ENTRY_SIZE]

        if len(entry) < GPT_ENTRY_SIZE:
            break

        # Extract fields from the partition entry
        partition_type_guid = entry[0:16]      # 16 bytes for partition type GUID
        unique_guid = entry[16:32]             # 16 bytes for unique partition GUID

        start_lba = struct.unpack("<Q", entry[32:40])[0]   # bytes 32-39 for starting LBA, little-endian unsigned long long
        end_lba = struct.unpack("<Q", entry[40:48])[0]     # bytes 40-47 for ending LBA, little-endian unsigned long long

        attributes = struct.unpack("<Q", entry[48:56])[0]  # bytes 48-55 for attributes, little-endian unsigned long long

        # Partition name (UTF-16LE)
        name_bytes = entry[56:128]                         # bytes 56-127 for partition name, UTF-16LE encoded
        partition_name = name_bytes.decode("utf-16le", errors="ignore").strip("\x00")

        # Skip empty entries
        if start_lba == 0 and end_lba == 0:    # if both start and end LBA are 0, it's an empty entry, so we can skip it
            continue

        partitions.append({              # storing the parsed partition entry as a dictionary in the list
            "start_lba": start_lba,
            "end_lba": end_lba,
            "partition_name": partition_name,
            "type_guid": partition_type_guid.hex()
        })

    return partitions  
# this returns a list of dictionaries, where each dictionary contains the starting LBA, ending LBA, partition name, 
# and type GUID for each parsed partition entry