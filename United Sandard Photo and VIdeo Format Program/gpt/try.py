# Program ini bernama PROGRAM REKAYASA RESOLUSI MULTIMEDIA. Program ini dibuat oleh Kali Paperline.
# Program ini adalah sebuah alat untuk mengurangi kebutuhan penyimpanan dengan cara mengubah resolusi foto dan video menjadi 720p.

import os
from pathlib import Path
import re
import PIL.Image as Image
import shutil

DEFAULT_PATH = '.'
SHORT_SIDE_FILE_LENGTH = 720

PHOTO_FILE_FORMAT = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.avif', '.gif'}
VIDEO_FILE_FORMAT = {'.mp4', '.mkv', '.m4v', '.mov', '.ts', '.webm', '.avi', '.wmv'}

PHOTO_OUTPUT_FORMAT = {'.png', '.gif'}
VIDEO_OUTPUT_FORMAT = {'.mp4'}

Image.MAX_IMAGE_PIXELS = None

# ==================== MAIN PROGRAM ====================

def Main():
    root = Path(DEFAULT_PATH)
    result = {}

    # 1. Scan direktori dan seleksi file
    for dp, _, fn in os.walk(root):
        p = Path(dp)
        files = []

        # Filter file media
        for f in fn:
            full_path = p / f
            if full_path.suffix.lower() in PHOTO_FILE_FORMAT | VIDEO_FILE_FORMAT:
                files.append(full_path)

        if files:
            # 2. Natural sort manual tanpa fungsi/lambda
            n = len(files)
            for i in range(n):
                for j in range(i + 1, n):
                    # Buat key untuk files[i]
                    parts_i = re.split(r'(\d+)', files[i].stem)
                    key_i = []
                    for part in parts_i:
                        try:
                            key_i.append(int(part))
                        except ValueError:
                            key_i.append(part.lower())

                    # Buat key untuk files[j]
                    parts_j = re.split(r'(\d+)', files[j].stem)
                    key_j = []
                    for part in parts_j:
                        try:
                            key_j.append(int(part))
                        except ValueError:
                            key_j.append(part.lower())

                    # Bandingkan dan tukar jika perlu
                    if key_i > key_j:
                        files[i], files[j] = files[j], files[i]

            result[p] = files

    # 3. Output simulasi rename file
    print("[*] PROGRAM REKAYASA MULTIMEDIA")
    for folder, files in result.items():
        print(f"[*] [{folder}]")
        counter_photo = 1
        counter_video = 1

        for f in files:
            ext = f.suffix.lower()
            if ext in PHOTO_FILE_FORMAT:
                new_name = f"{counter_photo}.png" if ext != '.gif' else f"{counter_photo}.gif"
                counter_photo += 1
            else:
                new_name = f"{counter_video}.mp4"
                counter_video += 1
            print(f"[+] {f.name} --- {new_name}")

if __name__ == '__main__':
    Main()
