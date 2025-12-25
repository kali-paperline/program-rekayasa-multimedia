import ffmpeg
from PIL import Image
import pathlib
import re

WORKING_DIRECTORY   = pathlib.Path('.')

SCAN_PHOTO_FORMAT   = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.gif'}
SCAN_VIDEO_FORMAT   = {'.mp4', '.mkv', '.mov', '.avi', '.flv', '.wmv', '.webm', '.ts'}

OUTPUT_PHOTO_FORMAT = {'.png', '.gif'}
OUTPUT_VIDEO_FORMAT = {'.mp4'}

def ScanDiretoryWithPathlib(ROOT_PATH):
	SCAN_RESULT = {}
	SORT_RESULT = {}

	for FILE_FOUND in ROOT_PATH.rglob('*'):
		if not FILE_FOUND.is_file():
			continue

		if FILE_FOUND.suffix.lower() not in (SCAN_PHOTO_FORMAT | SCAN_VIDEO_FORMAT):
			continue

		FILE_FOUND_PATH = FILE_FOUND.parent
		SCAN_RESULT.setdefault(FILE_FOUND_PATH, []).append(FILE_FOUND)

	for CURRENT_FOLDER, FILE_LIST in SCAN_RESULT.items():
		TEMPORARY_SORT = []

		for FILE in FILE_LIST:
			FILE_NAME = FILE.name
			NAME_PART = re.split(r'(\d+)', FILE_NAME)

			SORT_KEY  = []

			for PART in NAME_PART:
				if PART.isdigit():
					NUMBER_VALUE = int(PART)
					SORT_KEY.append(NUMBER_VALUE)

				else:
					TEXT_VALUE = PART.lower()
					SORT_KEY.append(TEXT_VALUE)

			TEMPORARY_SORT.append((SORT_KEY, FILE))

		TEMPORARY_SORT.sort()

		SORTED_FILE = []

		for SORTED_SCAN in TEMPORARY_SORT:
			SORTED_PATH = SORTED_SCAN[1]
			SORTED_FILE.append(SORTED_PATH)

		SORT_RESULT[CURRENT_FOLDER] = SORTED_FILE

	return SORT_RESULT

def ConvertImageWithPillow(FILE_PATH, OUTPUT_PATH):
	pass

def ConvertVideoWithFFMPEG(FILE_PATH, OUTPUT_PATH):
	pass