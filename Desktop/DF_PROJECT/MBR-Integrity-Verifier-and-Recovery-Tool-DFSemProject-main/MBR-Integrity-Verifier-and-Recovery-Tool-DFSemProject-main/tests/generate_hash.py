import hashlib
from core.disk_reader import read_mbr_from_image
from core.mbr_parser import extract_boot_code

# STEP 1: load CLEAN image
image_path = "mbr_test.vhd"   # or .img / .dd file

# STEP 2: read MBR
mbr = read_mbr_from_image(image_path)

# STEP 3: extract 440-byte boot code
boot_code = extract_boot_code(mbr)

# STEP 4: generate hash
hash_value = hashlib.sha256(boot_code).hexdigest()

print("YOUR KNOWN MBR HASH IS:")
print(hash_value)