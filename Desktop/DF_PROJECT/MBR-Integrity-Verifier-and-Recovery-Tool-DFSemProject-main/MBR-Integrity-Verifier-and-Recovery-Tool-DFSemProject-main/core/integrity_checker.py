"""
core/integrity_checker.py
=========================
Member 3: Integrity Verification Logic (MBR + GPT)
"""

import hashlib


# hash calulated through the gernate_hash.py script on a known clean MBR image (mbr_test.vhd) - this is our "golden hash" for integrity checks
KNOWN_MBR_HASH = "59019b8b59cffb325855cdc7716d38f8ce2112b9b027f2f8516992e2e686525b"

# ─────────────────────────────────────────────
# MBR INTEGRITY CHECK
# ─────────────────────────────────────────────
def check_mbr_integrity(mbr_dict: dict) -> dict:
    """
    Expects:
        mbr_dict from mbr_parser.py

    Uses:
        mbr_dict["boot_code"] (440 bytes)

    Returns:
        dict result for GUI + report
    """

    boot_code = mbr_dict["boot_code"]
    current_hash = hashlib.sha256(boot_code).hexdigest()

    is_valid = (current_hash == KNOWN_MBR_HASH)

    return {
        "type": "MBR",
        "status": "OK" if is_valid else "CORRUPTED",
        "match": is_valid,
        "current_hash": current_hash,
        "expected_hash": KNOWN_MBR_HASH
    }


# ─────────────────────────────────────────────
# GPT INTEGRITY CHECK
# ─────────────────────────────────────────────
def check_gpt_integrity(gpt_dict: dict) -> dict:
    """
    Simple GPT integrity verification:
    1. Check signature
    2. Check basic consistency
    """

    signature_ok = (gpt_dict.get("signature") == "EFI PART")

    # basic sanity checks
    backup_lba = gpt_dict.get("backup_lba", 0)
    current_lba = gpt_dict.get("current_lba", 0)

    structure_ok = backup_lba > 0 and current_lba >= 1

    if signature_ok and structure_ok:
        status = "OK"
    else:
        status = "CORRUPTED"

    return {
        "type": "GPT",
        "status": status,
        "signature_valid": signature_ok,
        "structure_valid": structure_ok
    }

# ─────────────────────────────────────────────
# COMBINED SYSTEM CHECK (FOR GUI)
# ─────────────────────────────────────────────
def full_integrity_report(mbr_dict: dict, gpt_dict: dict) -> dict:
    """
    Returns unified report for dashboard/demo.
    """

    mbr_result = check_mbr_integrity(mbr_dict)
    gpt_result = check_gpt_integrity(gpt_dict)

    return {
        "MBR": mbr_result,
        "GPT": gpt_result,
        "system_status": "SAFE"
        if mbr_result["status"] == "OK" and gpt_result["status"] == "OK"
        else "COMPROMISED"
    }