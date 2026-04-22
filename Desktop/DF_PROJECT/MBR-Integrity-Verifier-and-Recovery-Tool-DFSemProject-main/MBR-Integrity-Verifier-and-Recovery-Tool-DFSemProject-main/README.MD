MBR Integrity Verifier and Recovery Tool
========================================

A Python-based digital forensics utility for reading, verifying, parsing, and recoveringMaster Boot Record (MBR) and GPT data from forensic disk images and live physical disks.

---

1\. Tool Overview
----------------------

This tool provides raw sector-level access to disk structures critical in forensicinvestigations — including the Master Boot Record (MBR), Primary GPT Header, and Backup GPT Header.

The system is modular:
\
**Disk Reader Module** handles low-level disk access.
\
**MBR & GPT Parser Module** extracts structured forensic information from raw bytes.
\
**Integrity & Recovery Module** verifies and restores modified boot structures.
\
**GUI & Reporting Module** provides visualization and report generation.
    

The disk reading module (core/disk\_reader.py) forms the foundation of the system. It reads 512-byte sectors from:
 - Forensic images (.dd, .img, split .001–.00N)
 - Live physical disks (Windows \\\\.\\PhysicalDriveN)
    

Split forensic image formats are automatically detected and reassembled in memory. All functions strictly follow a forensic rule: 
> No modification, no printing, only raw byte extraction.

---

2\. Installation Instructions
-----------------------------

**Step 1 — Install Python 3.10 or higher**

Download from [https://www.python.org/downloads/](https://www.python.org/downloads/) and enable “Add to PATH”.

Verify:
```   
python --version   
```

**Step 2 — Project Structure**
```
   DFProject/  
   ├── core/  
   │   ├── disk_reader.py  
   │   ├── mbr_parser.py  
   │   ├── gpt_parser.py  
   ├── images/  
   │   │   ├── mbr_test.vhd  
   │   │   ├── gpt_test.vhd  
   │   │   └── README_IMAGES.txt  
   ├── tests/  
   │   ├── test_disk_reader.py  
   │   └── test_run_parser.py  
   └── main.py   `
```

**Step 3 — Load forensic images or VHD disks**
**IMP**: Place all .001 image segments or mounted VHD disk files inside images/.

**Step 4 — No external libraries required**
Only Python standard library is used.

---

3\. Dependencies and Prerequisites
----------------------------------
No external dependencies are required. It relies entirely on the following
Python standard library modules which come pre-installed with Python:
- `os` — file path resolution and size calculation
- `sys` — platform detection for live disk access
- `glob` — segment file discovery
- `struct` — reserved for binary parsing extensions
    

**Requirements:**
 - Python 3.10+
 - Windows (for live disk access)
 - Administrator privileges (for PhysicalDrive access only)
    
---

4\. Execution Steps
-------------------
**Running the test suite (recommended first step):**

```
cd DFProject
python tests/test_disk_reader.py
```

This will run six tests covering segment detection, MBR reading, GPT header reading,
backup GPT reading, live disk access, and error handling. All results are printed
with PASS/FAIL indicators.

**Using the module in code:**

```python
from core.disk_reader import read_mbr_from_image

mbr = read_mbr_from_image("images/clean_mbr.001")
# mbr is exactly 512 raw bytes
```

**Live disk access on Windows (must run PowerShell as Administrator):**

```python
from core.disk_reader import read_mbr_from_live

mbr = read_mbr_from_live(drive_number=0)
# 0 = PhysicalDrive0, 1 = PhysicalDrive1, and so on
```

**Getting image metadata:**

```python
from core.disk_reader import get_image_info

info = get_image_info("images/clean_mbr.001")
# Returns total size, sector count, segment list, and split flag
```

**Run full integration test:**
```   
python tests/test_run_parser.py   
```

**Read MBR:**
```python
from core.disk_reader 
import read_mbr_from_imagembr = read_mbr_from_image("images/mbr_test.vhd")   
```

**Parse MBR:**
```python
from core.mbr_parser 
import parse_partition_tablepartitions = parse_partition_table(mbr)   
```

**Parse GPT:**
```python
from core.gpt_parser 
import parse_gpt_headergpt_info = parse_gpt_header(gpt_bytes)   
```

---







5\. Platform Compatibility
--------------------------

### Windows 10 / 11

✔ Full support\
✔ Live disk reading supported (PhysicalDrive)\
✔ VHD and forensic images supported

### Linux / macOS

✔ Forensic images supported\
✔ VHD must be mounted manually\
❌ Live disk reading module disabled

---

6\. Integrity Verification & Recovery Module 

This module handles MBR integrity verification, corruption detection, and recovery using cryptographic hashing and forensic reference images.

 ** Generate Reference Hash **


This is a one-time setup step to create the trusted hash.

  python -m tests.generate_hash
Example Output:
MBR validation successful: Correct size (512 bytes)!

YOUR KNOWN MBR HASH IS:
59019b8b59cffb325855cdc7716d38f8ce2112b9b027f2f8516992e2e686525b
** Integrity Testing **
Run Integrity Check
python -m tests.run_integrity_test
 ** Output (Clean Image) **
{
  "type": "MBR",
  "status": "OK",
  "match": true,
  "current_hash": "59019b8b59cffb325855cdc7716d38f8ce2112b9b027f2f8516992e2e686525b",
  "expected_hash": "59019b8b59cffb325855cdc7716d38f8ce2112b9b027f2f8516992e2e686525b"
}
Output (Corrupted Image)
{
  "type": "MBR",
  "status": "CORRUPTED",
  "match": false,
  "current_hash": "0cdfb6d056c96b56a5aaa40b4776ca8a6078da7877b36458831f8389903db48d",
  "expected_hash": "59019b8b59cffb325855cdc7716d38f8ce2112b9b027f2f8516992e2e686525b"
}
** Corruption Simulation **

To simulate real forensic attack scenarios, a controlled modification is performed on the MBR image.

Example (Byte Modification):
** Simulating corruption by modifying one byte **
with open("images/mbr_test.vhd", "r+b") as f:
    f.seek(0)
    f.write(b"\x00")

This results in:

Change in boot code
Different SHA-256 hash
Integrity failure detection
# Recovery Mechanism

The recovery module restores the original MBR using a clean forensic reference image.

Recovery Steps:
1. Load clean forensic image
2. Extract original 440-byte boot code
3. Overwrite corrupted MBR boot sector
4. Recalculate hash
5. Re-verify integrity
# Run Recovery
python -m tests.test_recovery
** Recovery Output ** 
{
  "status": "RECOVERED",
  "message": "MBR boot code restored successfully"
}
** Post-Recovery Verification **

After recovery, integrity is re-checked to confirm restoration.

Output:
{
  "type": "MBR",
  "status": "OK",
  "match": true
}


7\. Troubleshooting
-----------------------

**`FileNotFoundError` when running the test**
The image path in `tests/test_disk_reader.py` is set to `images/clean_mbr.001`.
Make sure your segment files are inside a folder named `images/` at the project root
and that the file is named exactly `clean_mbr.001`.

**`ValueError: only got N bytes`**
One or more image segments are missing or corrupted. Confirm that all 18 segments
are present in the `images/` folder and that none of them are 0 bytes in size.
Re-export the image from FTK Imager if segments are damaged.

**`PermissionError: Access denied to \\.\PhysicalDrive0`**
The script is not running with Administrator privileges. Close PowerShell, right-click
it, select "Run as administrator", navigate back to the project folder, and re-run
the test.

**`FileNotFoundError` on `\\.\PhysicalDrive0`**
The drive index may be wrong. Open Disk Management (`diskmgmt.msc`) to confirm which
physical drive number corresponds to the disk you want to read, then pass that number
to `read_mbr_from_live()`.

**`OSError: only supported on Windows`**
You called `read_mbr_from_live()` on Linux or macOS. Use `read_mbr_from_image()`
with the raw device path instead, as described in the Platform Compatibility section.

**Segments not being detected automatically**
The auto-detection looks for files sharing the same base name with purely numeric
extensions (`.001`, `.002`, etc.). If your files use a different naming convention,
rename them to follow this pattern or pass each path manually.

---

7\. Team Members
-----------------------
Syeda Shanzay Shah 23I-2016\
Sarita Sangrez 23I-2088\
Rumaisah Haroon 23I-2106\
Fatima Naeem 23I-2046
