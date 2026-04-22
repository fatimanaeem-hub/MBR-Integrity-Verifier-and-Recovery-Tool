"""
tests/test_disk_reader.py
=========================
Verification tests for Member 1 — Disk & Image Handling

Run from project root:
    python tests/test_disk_reader.py

All tests print PASS / FAIL.
No pytest required.
"""

import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.disk_reader import (
    read_mbr_from_image,
    read_gpt_header_from_image,
    read_backup_gpt_header,
    read_mbr_from_live,
    read_gpt_header_from_live,
    get_image_info,
    SECTOR_SIZE,
)

# Path of your first image segment 
IMAGE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "images", "gpt_test.vhd"
)



def header(title: str):
    print(f"\n{'═'*60}")
    print(f"  {title}")
    print('═'*60)


def check(label: str, condition: bool, detail: str = ""):
    status = "PASS" if condition else "FAIL"
    print(f"  {status}  {label}")
    if detail:
        print(f"         → {detail}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 1: Image info / segment detection
# ─────────────────────────────────────────────────────────────────────────────
def test_image_info():
    header("TEST 1 — Image Info & Segment Detection")
    try:
        info = get_image_info(IMAGE_PATH)
        check("Segments detected",       len(info["segments"]) >= 1,
              f"{len(info['segments'])} segment(s) found")
        check("Total size > 0",          info["total_size"] > 0,
              f"{info['total_size']:,} bytes")
        check("Total sectors > 0",       info["total_sectors"] > 0,
              f"{info['total_sectors']:,} sectors")
        check("Split flag correct",      isinstance(info["is_split"], bool),
              f"is_split = {info['is_split']}")
        print(f"\n  Segments:")
        for s in info["segments"]:
            print(f"    {os.path.basename(s)}")
    except Exception as e:
        print(f"  Exception: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 2: MBR from image
# ─────────────────────────────────────────────────────────────────────────────
def test_mbr_from_image():
    header("TEST 2 — read_mbr_from_image()")
    try:
        mbr = read_mbr_from_image(IMAGE_PATH)

        check("Returns bytes",       isinstance(mbr, bytes))
        check("Exactly 512 bytes",   len(mbr) == SECTOR_SIZE,
              f"Got {len(mbr)} bytes")
        check("MBR signature 55 AA", mbr[510:512] == b'\x55\xAA',
              f"Last 2 bytes: {mbr[510:512].hex().upper()}")

        print(f"\n  First 16 bytes (hex):")
        print(f"    {mbr[:16].hex(' ').upper()}")

        print(f"\n  Partition table entries (bytes 446–509):")
        for i in range(4):
            entry = mbr[446 + i*16 : 446 + (i+1)*16]
            status = entry[0]
            ptype  = entry[4]
            if ptype != 0x00:
                print(f"    Partition {i+1}: type=0x{ptype:02X}  "
                      f"status=0x{status:02X}  raw={entry.hex().upper()}")
            else:
                print(f"    Partition {i+1}: (empty)")

    except Exception as e:
        print(f"Exception: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 3: GPT primary header from image
# ─────────────────────────────────────────────────────────────────────────────
def test_gpt_from_image():
    header("TEST 3 — read_gpt_header_from_image() [LBA 1]")
    try:
        gpt = read_gpt_header_from_image(IMAGE_PATH)

        check("Returns bytes",       isinstance(gpt, bytes))
        check("Exactly 512 bytes",   len(gpt) == SECTOR_SIZE,
              f"Got {len(gpt)} bytes")

        # GPT signature is "EFI PART" = 45 46 49 20 50 41 52 54
        EFI_SIGNATURE = b'EFI PART'
        is_gpt = gpt[:8] == EFI_SIGNATURE
        check("GPT signature 'EFI PART'", is_gpt,
              f"First 8 bytes: {gpt[:8].hex().upper()} "
              f"({'GPT disk' if is_gpt else 'not GPT — likely MBR-only disk, that is fine'})")

        print(f"\n  First 16 bytes (hex):")
        print(f"    {gpt[:16].hex(' ').upper()}")

    except Exception as e:
        print(f"Exception: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 4: Backup GPT header from image
# ─────────────────────────────────────────────────────────────────────────────
def test_backup_gpt_from_image():
    header("TEST 4 — read_backup_gpt_header() [Last Sector]")
    try:
        backup = read_backup_gpt_header(IMAGE_PATH)

        check("Returns bytes",     isinstance(backup, bytes))
        check("Exactly 512 bytes", len(backup) == SECTOR_SIZE,
              f"Got {len(backup)} bytes")

        EFI_SIGNATURE = b'EFI PART'
        is_gpt_backup = backup[:8] == EFI_SIGNATURE
        check("Backup GPT signature",  is_gpt_backup,
              f"First 8 bytes: {backup[:8].hex().upper()} "
              f"({'backup GPT found' if is_gpt_backup else 'not a GPT backup — expected on MBR disks'})")

        print(f"\n  First 16 bytes (hex):")
        print(f"    {backup[:16].hex(' ').upper()}")

    except Exception as e:
        print(f"Exception: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 5: Live disk (Windows only)
# ─────────────────────────────────────────────────────────────────────────────
def test_live_disk():
    header("TEST 5 — read_mbr_from_live() [Windows only]")
    import platform
    if platform.system() != "Windows":
        print("  ⏭  SKIPPED — Not running on Windows")
        return
    try:
        mbr = read_mbr_from_live(0)
        check("Returns bytes",       isinstance(mbr, bytes))
        check("Exactly 512 bytes",   len(mbr) == SECTOR_SIZE,
              f"Got {len(mbr)} bytes")
        check("MBR signature 55 AA", mbr[510:512] == b'\x55\xAA',
              f"Last 2 bytes: {mbr[510:512].hex().upper()}")
        print(f"\n  First 16 bytes (hex):")
        print(f"    {mbr[:16].hex(' ').upper()}")
    except PermissionError as e:
        print(f"  ⚠  PermissionError (run as Admin): {e}")
    except Exception as e:
        print(f"Exception: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 6: Error handling
# ─────────────────────────────────────────────────────────────────────────────
def test_error_handling():
    header("TEST 6 — Error Handling")

    # Non-existent file
    try:
        read_mbr_from_image("/nonexistent/path/fake.dd")
        check("FileNotFoundError raised", False)
    except FileNotFoundError:
        check("FileNotFoundError on missing file", True)
    except Exception as e:
        check("FileNotFoundError on missing file", False, str(e))

    # Truncated / tiny file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".dd", delete=False) as tmp:
        tmp.write(b'\x00' * 100)          # only 100 bytes — too small for MBR
        tmp_path = tmp.name
    try:
        read_mbr_from_image(tmp_path)
        check("ValueError on truncated image", False)
    except ValueError:
        check("ValueError on truncated image", True)
    except Exception as e:
        check("ValueError on truncated image", False, str(e))
    finally:
        os.unlink(tmp_path)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not os.path.isfile(IMAGE_PATH):
        print(f"\n Image not found at: {IMAGE_PATH}")
        print("   Edit IMAGE_PATH in this script to point to your .001 file.")
        print("   (expected location: DFProject/images/clean_mbr.001)")
        sys.exit(1)

    print("\n" + "█"*60)
    print("  Member 1 — Disk Reader Module Tests")
    print("  MBR Integrity Verifier & Recovery Tool")
    print("█"*60)

    test_image_info()
    test_mbr_from_image()
    test_gpt_from_image()
    test_backup_gpt_from_image()
    test_live_disk()
    test_error_handling()

    print("\n" + "═"*60)
    print("  All tests complete.")
    print("═"*60 + "\n")