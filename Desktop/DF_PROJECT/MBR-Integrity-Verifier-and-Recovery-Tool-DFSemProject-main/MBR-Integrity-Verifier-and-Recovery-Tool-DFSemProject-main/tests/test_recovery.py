from core.recovery import recover_mbr
from core.disk_reader import read_mbr_from_image
from core.mbr_parser import extract_boot_code
from core.integrity_checker import check_mbr_integrity

corrupted_image = "mbr_test.vhd"
clean_image = "clean_mbr.vhd"

# STEP 1: recover
result = recover_mbr(corrupted_image, clean_image)
print(result)

# STEP 2: verify again
mbr = read_mbr_from_image(corrupted_image)
boot_code = extract_boot_code(mbr)

mbr_dict = {"boot_code": boot_code}

print(check_mbr_integrity(mbr_dict))