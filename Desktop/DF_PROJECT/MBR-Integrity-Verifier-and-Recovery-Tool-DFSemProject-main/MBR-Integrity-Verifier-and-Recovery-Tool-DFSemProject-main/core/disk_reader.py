"""
core/disk_reader.py
===================
"""
 
import os
import sys
import glob
import struct
 
 
# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
 
SECTOR_SIZE = 512          # Standard sector size in bytes
LBA_MBR     = 0           # MBR lives at LBA 0 (byte offset 0)
LBA_GPT     = 1           # Primary GPT header at LBA 1 (byte offset 512)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────────────────────
 
def _read_sector_from_file(file_obj, lba: int) -> bytes:
    """
    Seek to the given LBA inside an already-open file object and read
    exactly SECTOR_SIZE (512) bytes.
 
    Args:
        file_obj : open binary file handle (mode 'rb')
        lba      : Logical Block Address (0 = first sector)
 
    Returns:
        bytes of length SECTOR_SIZE
 
    Raises:
        ValueError  : if fewer than 512 bytes could be read (truncated image)
        IOError     : on seek/read failure
    """
    offset = lba * SECTOR_SIZE
    file_obj.seek(offset)
    data = file_obj.read(SECTOR_SIZE)
 
    if len(data) < SECTOR_SIZE:
        raise ValueError(
            f"Expected {SECTOR_SIZE} bytes at LBA {lba} (offset {offset}), "
            f"but only got {len(data)} bytes. "
            f"The image may be truncated or the LBA is out of range."
        )
    return data
 
 
def _resolve_split_image_segments(base_path: str) -> list[str]:
    """
    Given a path like  /some/dir/clean_mbr.001  (or .dd / .img),
    return a sorted list of all segment paths that belong to the same image.

    """
    if not os.path.isfile(base_path):
        raise FileNotFoundError(f"Image file not found: {base_path!r}")
 
    # Try to detect a numeric extension like .001
    root, ext = os.path.splitext(base_path)
    if ext and ext[1:].isdigit():
        # Glob for all numeric siblings: .001 .002 … .999
        pattern = root + ".*"
        candidates = sorted(
            p for p in glob.glob(pattern)
            if os.path.splitext(p)[1][1:].isdigit()
        )
        if candidates:
            return candidates
 
    # Not split — return the single file
    return [base_path]
 
 
def _open_split_image(base_path: str):
    """
    Context-manager-friendly generator that yields a *virtual* file-like
    object capable of reading across split image segments seamlessly.
    """
    segments = _resolve_split_image_segments(base_path)
    return _SplitImageReader(segments)
 
 
class _SplitImageReader:
    """
    Reads sectors across an ordered list of raw image segment files.
 
    Calculates each segment's byte size once on init, then for any given
    byte offset it figures out which file to open and at what position.
    """
 
    def __init__(self, segment_paths: list[str]):
        self._segments = segment_paths
        # Pre-compute cumulative byte offsets for each segment
        self._sizes: list[int] = []
        self._cumulative: list[int] = []  # cumulative END offsets
        total = 0
        for p in segment_paths:
            sz = os.path.getsize(p)
            self._sizes.append(sz)
            total += sz
            self._cumulative.append(total)
        self._total_size = total
 
    def total_size(self) -> int:
        """Total byte size of the reassembled image."""
        return self._total_size
 
    def read_bytes(self, offset: int, length: int) -> bytes:
        """
        Read `length` bytes starting at absolute byte `offset` in the
        reassembled image, spanning segment boundaries if necessary.
        """
        if offset + length > self._total_size:
            raise ValueError(
                f"Read of {length} bytes at offset {offset} exceeds "
                f"image size {self._total_size}."
            )
 
        result = bytearray()
        remaining = length
        pos = offset
 
        for i, seg_path in enumerate(self._segments):
            seg_start = self._cumulative[i] - self._sizes[i]
            seg_end   = self._cumulative[i]
 
            if pos >= seg_end:
                continue                       # haven't reached this segment yet
            if pos + remaining <= seg_start:
                break                          # already past what we need
 
            # How many bytes to read from this segment
            read_from  = pos - seg_start       # position inside this file
            available  = seg_end - pos         # bytes left in this file from pos
            to_read    = min(remaining, available)
 
            with open(seg_path, "rb") as fh:
                fh.seek(read_from)
                chunk = fh.read(to_read)
                if len(chunk) != to_read:
                    raise IOError(
                        f"Short read from segment {seg_path!r}: "
                        f"expected {to_read}, got {len(chunk)}."
                    )
                result.extend(chunk)
 
            pos       += to_read
            remaining -= to_read
            if remaining == 0:
                break
 
        return bytes(result)
 
    def read_sector(self, lba: int) -> bytes:
        """Read exactly 512 bytes at the given LBA."""
        return self.read_bytes(lba * SECTOR_SIZE, SECTOR_SIZE)
 
    def close(self):
        """No persistent handles to close, but provided for API symmetry."""
        pass
 
 
# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API — FORENSIC IMAGE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────
 
def read_mbr_from_image(path: str) -> bytes:
    """
    Read the Master Boot Record (LBA 0) from a forensic disk image.

    """
    reader = _open_split_image(path)
    try:
        return reader.read_sector(LBA_MBR)
    finally:
        reader.close()
 
 
def read_gpt_header_from_image(path: str) -> bytes:
    """
    Read the Primary GPT Header located at LBA 1 (byte offset 512).

    """
    reader = _open_split_image(path)
    try:
        return reader.read_sector(LBA_GPT)
    finally:
        reader.close()
 
 
def read_backup_gpt_header(path: str) -> bytes:
    """
    Read the Backup GPT Header from the very last 512-byte sector of
    the image.
 
    """
    reader = _open_split_image(path)
    try:
        total = reader.total_size()
        if total < SECTOR_SIZE:
            raise ValueError(
                f"Image too small ({total} bytes) to contain even one sector."
            )
        last_offset = total - SECTOR_SIZE
        return reader.read_bytes(last_offset, SECTOR_SIZE)
    finally:
        reader.close()
 
 
def get_image_info(path: str) -> dict:
    """
    Return metadata about the image without reading full content.

    """
    reader = _open_split_image(path)
    try:
        total = reader.total_size()
        segs  = reader._segments
        return {
            "segments"     : segs,
            "total_size"   : total,
            "total_sectors": total // SECTOR_SIZE,
            "is_split"     : len(segs) > 1,
        }
    finally:
        reader.close()
 
 
# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API — LIVE DISK FUNCTIONS  (Windows only)
# ─────────────────────────────────────────────────────────────────────────────
 
def read_mbr_from_live(drive_number: int = 0) -> bytes:
    """
    Read the Master Boot Record (LBA 0) from a live physical disk.
 
        WINDOWS ONLY — requires Administrator privileges.
        On Linux/macOS use read_mbr_from_image() with /dev/sdX instead.

    """
    if sys.platform != "win32":
        raise OSError(
            "read_mbr_from_live() is only supported on Windows. "
            "On Linux/macOS, pass the device path (e.g. '/dev/sda') "
            "to read_mbr_from_image() instead."
        )
 
    drive_path = f"\\\\.\\PhysicalDrive{drive_number}"
 
    try:
        # Open the raw device — requires elevated privileges
        with open(drive_path, "rb") as fh:
            data = fh.read(SECTOR_SIZE)
    except PermissionError:
        raise PermissionError(
            f"Access denied to {drive_path}. "
            "Please run the tool as Administrator."
        )
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Physical drive not found: {drive_path}. "
            f"Check that PhysicalDrive{drive_number} exists."
        )
 
    if len(data) < SECTOR_SIZE:
        raise ValueError(
            f"Expected 512 bytes from {drive_path} but only got {len(data)}. "
            "The drive may be reporting a non-standard sector size."
        )
 
    return data
 
 
def read_gpt_header_from_live(drive_number: int = 0) -> bytes:
    """
    Read the Primary GPT Header (LBA 1) from a live physical disk.
 
    WINDOWS ONLY — requires Administrator privileges.

    """
    if sys.platform != "win32":
        raise OSError(
            "read_gpt_header_from_live() is only supported on Windows."
        )
 
    drive_path = f"\\\\.\\PhysicalDrive{drive_number}"
 
    try:
        with open(drive_path, "rb") as fh:
            # Skip LBA 0 (512 bytes) to reach LBA 1
            fh.seek(SECTOR_SIZE)
            data = fh.read(SECTOR_SIZE)
    except PermissionError:
        raise PermissionError(
            f"Access denied to {drive_path}. Run as Administrator."
        )
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Physical drive not found: {drive_path}."
        )
 
    if len(data) < SECTOR_SIZE:
        raise ValueError(
            f"Expected 512 bytes at LBA 1 of {drive_path}, got {len(data)}."
        )
 
    return data
    

# helper function to read the GPT partition table (LBA 2) from the image, which is needed for the GPT partition table test in test_run_parser.py
def read_gpt_table_from_image(path: str) -> bytes:
    reader = _open_split_image(path)
    try:
        # LBA 2 starts at 1024 bytes
        return reader.read_bytes(1024, 128 * 4)
    finally:
        reader.close()