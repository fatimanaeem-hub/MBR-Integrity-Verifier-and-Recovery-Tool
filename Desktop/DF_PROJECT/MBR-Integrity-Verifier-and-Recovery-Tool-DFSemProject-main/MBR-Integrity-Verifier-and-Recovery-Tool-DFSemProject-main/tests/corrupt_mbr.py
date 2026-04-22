# this script modifies the MBR image to simulate corruption for testing the integrity checker

file_path = "mbr_test.vhd"

with open(file_path, "r+b") as f:
    f.seek(0)      # start of MBR
    f.write(b"\x00")  # corrupt 1 byte

print("MBR corrupted (1 byte modified)")