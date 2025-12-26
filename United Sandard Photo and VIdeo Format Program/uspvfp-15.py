# UNITED STANDARD PHOTO AND VIDEO FORMAT PROGRAM 1.5
# 
# Import LIbrary

import ffmpeg
import os
from PIL import Image
import pathlib
import re

# Define Variable

DEFAULT_WORKING_DIRECTORY = pathlib.Path('.')
DEFAULT_SHORT_SIDE        = 720

SCAN_PHOTO_FORMAT         = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.gif'}
SCAN_VIDEO_FORMAT         = {'.mp4',  '.mkv', '.mov', '.avi',  '.flv',  '.wmv', '.webm', '.ts'}
SCAN_ALL_FORMAT           = SCAN_PHOTO_FORMAT | SCAN_VIDEO_FORMAT

ALLOWED_PHOTO_FORMAT      = {'.png', '.gif'}
ALLOWER_VIDEO_FORMAT      = {'.mp4'}

# Define Function

def ScanDirectoryWithPathlib(ROOT_PATH):
	UNSORTED_SCAN_RESULT = {}

	for FILE in ROOT_PATH.rglob('*'):
		if not FILE.is_file():
			continue

		if FILE.suffix.lower() not in SCAN_ALL_FORMAT:
			continue

		FILE_PATH = FILE.parent
		UNSORTED_SCAN_RESULT.setdefault(FILE_PATH, []).append(FILE)

	return UNSORTED_SCAN_RESULT

def ConvertPhotoWithPillow(FILE_PATH, OUTPUT_PATH):
	print('PROCESS')

def ConvertVideoWithFFMPEG(FILE_PATH, OUTPUT_PATH):
	print('PROCESS')

def ConvertionRenameLogic(FILE_LIST):
	SORTED_SCAN_RESULT   = {}

	for FOLDER, FILE_LIST in FILE_LIST.items():
		TEMPORARY = []

		for FILE in FILE_LIST:
			FILE_NAME = FILE.name
			PART_NAME = re.split(r'(\d+)', FILE_NAME)

			SORT_KEY = []

			for PART in PART_NAME:
				if PART.isdigit():
					NUMBER_VALUE = int(PART)
					SORT_KEY.append(NUMBER_VALUE)

				else:
					TEXT_VALUE = PART.lower()
					SORT_KEY.append(TEXT_VALUE)

			TEMPORARY.append((SORT_KEY, FILE))

		TEMPORARY.sort()

		for FILE in TEMPORARY:
			SORTED_SCAN_RESULT.setdefault(FOLDER, []).append(FILE[1])

	for FOLDER, FILE_LIST in SORTED_SCAN_RESULT.items():
		print('[+]%s' % FOLDER)
		PHOTO_COUNT        = 1
		GIF_COUNT          = 1
		VIDEO_COUNT        = 1

		for FILE in FILE_LIST:
			if FILE.suffix.lower() in SCAN_PHOTO_FORMAT and FILE.suffix.lower() != '.gif':
				if FILE.stem.isdigit():
					TEMP_FILE = FILE.parent / ('TEMP_%s' % FILE.name)
					os.rename(FILE, TEMP_FILE)
					ConvertPhotoWithPillow(TEMP_FILE, '%s.png' % PHOTO_COUNT)
					print('%.32s --- %.32s --- %.32s.png' % (FILE, TEMP_FILE, PHOTO_COUNT))
					PHOTO_COUNT += 1

				else:
					ConvertPhotoWithPillow(FILE, '%s.png' % PHOTO_COUNT)
					print('%.32s --- %.32s.png' % (FILE, PHOTO_COUNT))
					PHOTO_COUNT += 1

			elif FILE.suffix.lower() in SCAN_PHOTO_FORMAT and FILE.suffix.lower() == '.gif':
				if FILE.stem.isdigit():
					TEMP_FILE = FILE.parent / ('TEMP_%s' % FILE.name)
					os.rename(FILE, TEMP_FILE)
					ConvertPhotoWithPillow(TEMP_FILE, '%s.gif' % GIF_COUNT)
					print('%.32s --- %.32s --- %.32s.gif' % (FILE, TEMP_FILE, GIF_COUNT))
					GIF_COUNT += 1

				else:
					ConvertPhotoWithPillow(TEMP_FILE, '%s.gif' % GIF_COUNT)
					print('%.32s --- %.32s.gif' % (FILE, GIF_COUNT))
					GIF_COUNT += 1

			elif FILE.suffix.lower() in SCAN_VIDEO_FORMAT:
				if FILE.stem.isdigit():
					TEMP_FILE = FILE.parent / ('TEMP_%s' % FILE.name)
					ConvertVideoWithFFMPEG(FILE, '%s.mp4' % VIDEO_COUNT)
					print('%.32s --- %.32s --- %.32s.mp4' % (FILE, TEMP_FILE, VIDEO_COUNT))
					VIDEO_COUNT += 1

				else:
					ConvertVideoWithFFMPEG(FILE, '%s.mp4' % VIDEO_COUNT)
					print('%.32s --- %.32s.mp4' % (FILE, VIDEO_COUNT))
					VIDEO_COUNT += 1

# Main Program

def Main():
	ConvertionRenameLogic(ScanDirectoryWithPathlib(DEFAULT_WORKING_DIRECTORY))

if __name__ == '__main__':
	Main()