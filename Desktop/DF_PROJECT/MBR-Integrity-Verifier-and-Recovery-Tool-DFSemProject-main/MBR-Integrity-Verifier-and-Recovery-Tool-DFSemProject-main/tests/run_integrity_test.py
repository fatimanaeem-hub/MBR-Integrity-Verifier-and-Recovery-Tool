from core.disk_reader import read_mbr_from_image
from core.mbr_parser import extract_boot_code
from core.mbr_parser import validate_mbr
from core.mbr_parser import parse_partition_table

from core.integrity_checker import check_mbr_integrity

# 1. Load image
image_path = "mbr_test.vhd"

mbr_bytes = read_mbr_from_image(image_path)

# 2. Extract boot code (440 bytes)
boot_code = extract_boot_code(mbr_bytes)

# 3. Build dictionary (THIS is what Member 2 would normally do)
mbr_dict = {
    "boot_code": boot_code
}

# 4. Run YOUR function (Member 3 work)
result = check_mbr_integrity(mbr_dict)

# 5. Print result
print(result)