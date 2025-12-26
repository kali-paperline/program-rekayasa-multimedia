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
# 5. time
# 6. subprocess
# 7. sys

# Import File

import ffmpeg as ff
import os
import pathlib as pl
from PIL import Image as im
import time as ti
import subprocess as sp
import sys

# Define Variable

DEFAULT_WORKING_DIRECTORY_PATH = '.'

PHOTO_CONVERT_EXTENSION = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp', '.gif'}
VIDEO_CONVERT_EXTENSION = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.ts', '.m4v'}

ALLOWED_IMAGE_FORMATS = {'.png', '.gif'}
ALLOWED_VIDEO_FORMATS = {'.mp4'}

ALL_SUPPORTED_EXTENSION = PHOTO_CONVERT_EXTENSION | VIDEO_CONVERT_EXTENSION

# Define Function

def PathRecursiveScanFunction(ROOT_PATH):
	FILES_FOUND = []

	for PATH in pl.Path(ROOT_PATH).rglob("*"):
		if PATH.is_file():
			if PATH.suffix.lower() in ALL_SUPPORTED_EXTENSION:
				FILES_FOUND.append(PATH)

	return FILES_FOUND

def InitStat():
	STAT = {}

	for EXTENSION in ALL_SUPPORTED_EXTENSION:
		STAT[EXTENSION] = {
			"found": 0,
			"convert": 0,
			"skip": 0,
			"error": 0
		}

	return STAT

# Main Program

def Main():
	STAT = InitStat()

	print("[*] Scan direktori:", os.path.abspath(DEFAULT_WORKING_DIRECTORY_PATH))

	FILES_IN_DIRECTORY = PathRecursiveScanFunction(DEFAULT_WORKING_DIRECTORY_PATH)

	for FILE in FILES_IN_DIRECTORY:
		EXTENSION = FILE.suffix.lower()
		if EXTENSION in STAT:
			STAT[EXTENSION]["found"] = STAT[EXTENSION]["found"] + 1

	print("+==========+=========+=========+=========+=========+")
	print("| FILE     | FOUND   | CONVERT | SKIP    | ERROR   |")
	print("+----------+---------+---------+---------+---------+")

	TOTAL_FOUND = TOTAL_CONVERT = TOTAL_SKIP = TOTAL_ERROR = 0

	for EXTENSION in sorted(STAT.keys()):
		DATA = STAT[EXTENSION]

		print("| %-8s | %-7d | %-7d | %-7d | %-7d |" % (EXTENSION.replace(".", "").upper(), DATA["found"], DATA["convert"], DATA["skip"], DATA["error"]))

		TOTAL_FOUND   = TOTAL_FOUND   + DATA["found"]
		TOTAL_CONVERT = TOTAL_CONVERT + DATA["convert"]
		TOTAL_SKIP    = TOTAL_SKIP    + DATA["skip"]
		TOTAL_ERROR   = TOTAL_ERROR   + DATA["error"]

	print("+----------+---------+---------+---------+---------+")
	print("| TOTAL    | %-7d | %-7d | %-7d | %-7d |" % (TOTAL_FOUND, TOTAL_CONVERT, TOTAL_SKIP, TOTAL_ERROR))
	print("+----------+---------+---------+---------+---------+")

if __name__ == '__main__':
	Main()
