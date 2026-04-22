"""
core/__init__.py
================
MBR Integrity Verifier and Recovery Tool
CY-2002/3006 Digital Forensics — Semester Project

Exposes Member 1's disk reading functions at the package level
so other members can import them directly:

    from core import read_mbr_from_image
    from core import read_gpt_header_from_image
"""

from core.disk_reader import (
    read_mbr_from_image,
    read_gpt_header_from_image,
    read_backup_gpt_header,
    read_mbr_from_live,
    read_gpt_header_from_live,
    get_image_info,
    SECTOR_SIZE,
)

__all__ = [
    "read_mbr_from_image",
    "read_gpt_header_from_image",
    "read_backup_gpt_header",
    "read_mbr_from_live",
    "read_gpt_header_from_live",
    "get_image_info",
    "SECTOR_SIZE",
]