import os
import uuid

# Direktori kerja otomatis
FOLDER_PATH = os.getcwd()
EXTENSION = ".png"

# Input angka awal
start_number = int(input("Masukkan angka awal penomoran: "))

# Ambil semua file PNG (hanya file, bukan folder)
files = [
    f for f in os.listdir(FOLDER_PATH)
    if f.lower().endswith(EXTENSION) and os.path.isfile(f)
]

# Urutkan supaya konsisten
files.sort()

# =====================
# TAHAP 1: Rename sementara
# =====================
temp_mapping = []

for filename in files:
    temp_name = f"__tmp_{uuid.uuid4().hex}{EXTENSION}"
    old_path = os.path.join(FOLDER_PATH, filename)
    temp_path = os.path.join(FOLDER_PATH, temp_name)

    os.rename(old_path, temp_path)
    temp_mapping.append(temp_name)

# =====================
# TAHAP 2: Rename final
# =====================
current_number = start_number

for temp_name in temp_mapping:
    old_path = os.path.join(FOLDER_PATH, temp_name)
    new_name = f"{current_number}{EXTENSION}"
    new_path = os.path.join(FOLDER_PATH, new_name)

    os.rename(old_path, new_path)
    current_number += 1

print("Selesai.")
print("Total file diproses:", len(temp_mapping))
