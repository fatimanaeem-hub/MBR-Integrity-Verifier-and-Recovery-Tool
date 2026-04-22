from core.disk_reader import read_gpt_header_from_image
from core.gpt_parser import parse_gpt_header
from core.integrity_checker import check_gpt_integrity

image_path = "gpt_test.vhd"

gpt_bytes = read_gpt_header_from_image(image_path)
gpt_dict = parse_gpt_header(gpt_bytes)

result = check_gpt_integrity(gpt_dict)

print(result)