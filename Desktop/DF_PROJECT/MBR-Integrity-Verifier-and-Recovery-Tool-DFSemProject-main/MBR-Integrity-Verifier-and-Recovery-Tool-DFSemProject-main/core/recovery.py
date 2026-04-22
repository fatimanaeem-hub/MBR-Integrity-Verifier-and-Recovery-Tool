from core.disk_reader import read_mbr_from_image
from core.mbr_parser import extract_boot_code

def recover_mbr(image_path: str, clean_image_path: str) -> dict:
    """
    Restores MBR boot code from clean image into corrupted image.
    """

    # 1. read clean boot code
    clean_mbr = read_mbr_from_image(clean_image_path)
    clean_boot_code = extract_boot_code(clean_mbr)

    # 2. overwrite corrupted image
    with open(image_path, "r+b") as f:
        f.seek(0)  # start of disk (LBA 0)
        f.write(clean_boot_code)  # restore first 440 bytes

    return {
        "status": "RECOVERED",
        "message": "MBR boot code restored successfully"
    }