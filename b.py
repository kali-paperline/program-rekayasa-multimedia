# Program ini bernama PROGRAM REKAYASA RESOLUSI MULTIMEDIA. Program ini dibuat oleh Kali Paperline.
# Program ini adalah sebuah alat untuk mengurangi kebutuhan penyimpanan dengan cara mengubah resolusi foto dan video menjadi 720p.
#
# Alur Kerja Program:
# 1. Program melakukan scan direktori kerja dengan modul pathlib hingga sub direktori terdalam.
# 2. Program melakukan seleksi pada file - file yang ditemukan.
# 3. Program melakukan rekayasa pada file - file sesuai dengan perlakuan yang telah ditentukan sebelumnya.
#
# Kondisi Tujuan Program:
# 1. Semua file foto dan video beresolusi <=720p.
# 2. Semua file foto dan video memiliki nama string urut.
# 3. Semua file .gif memiliki semua frame yang berfungsi dengan baik sesuai syarat lainnya
#
# Pustaka Python 3 yang digunakan:
# 1. ffmpeg
# 2. os
# 3. pathlib
# 4. PIL
# 5. re
# 6. time
# 7. subprocess
# 8. sys

# Import File

import ffmpeg as ff
import os
import pathlib as pl
from PIL import Image as im
import re
import time as ti
import subprocess as sp
import sys

# Define Variable

DEFAULT_WORKING_DIRECTORY_PATH = pl.Path(os.getcwd())

PHOTO_CONVERT_EXTENSION        = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp', '.gif'}
VIDEO_CONVERT_EXTENSION        = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.ts', '.m4v'}

ALLOWED_IMAGE_FORMATS          = {'.png', '.gif'}
ALLOWED_VIDEO_FORMATS          = {'.mp4'}

ALL_SUPPORTED_EXTENSION        = PHOTO_CONVERT_EXTENSION | VIDEO_CONVERT_EXTENSION

# Define Function

def PathScanFunction(ROOT_PATH):
	PATH_SCAN_RESULT = {}

	for DIRECTORY_LIST, SUBDIRECTORY_LIST, FILE_FOUND in os.walk(ROOT_PATH):
		DIRECTORY_PATH = pl.Path(DIRECTORY_LIST)
		FILE_LIST      = []

		for FILE in FILE_FOUND:
			FULL_PATH_FILE = DIRECTORY_PATH / FILE
			FILE_EXTENSION = FULL_PATH_FILE.suffix.lower()

			if FILE_EXTENSION in PHOTO_CONVERT_EXTENSION | VIDEO_CONVERT_EXTENSION:
				FILE_LIST.append(FULL_PATH_FILE)

		if FILE_LIST:
			SORTER = []
			for FILE_PATH in FILE_LIST:
				pass
			FILE_LIST                        = sorted(FILE_LIST)
			PATH_SCAN_RESULT[DIRECTORY_PATH] = FILE_LIST

	return PATH_SCAN_RESULT

# Main Program

def Main():
	FILE_DIRECTORY_LIST      = PathScanFunction(DEFAULT_WORKING_DIRECTORY_PATH)
	MEDIA_CONVERTION_SUCCESS = MEDIA_CONVERTION_SKIP = MEDIA_CONVERTION_ERROR = 0

	print("[*] PROGRAM REKAYASA MULTIMEDIA")
	
	for DIRECTORY_LIST, FILE_LIST in FILE_DIRECTORY_LIST.items():
		print("[+] %s" % DIRECTORY_LIST)

		FILE_COUNTER = {}

		for FILE in FILE_LIST:
			print("   [+] %.100s" % FILE)

if __name__ == '__main__':
	Main()