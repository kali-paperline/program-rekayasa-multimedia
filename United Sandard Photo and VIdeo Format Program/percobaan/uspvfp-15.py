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
	try:
		IMAGE_FILE                      = Image.open(FILE_PATH)

		ORIGINAL_WIDTH, ORIGINAL_HEIGHT = IMAGE_FILE.size
		IMAGE_SHORT_SIZE                = min(ORIGINAL_WIDTH, ORIGINAL_HEIGHT)

		if IMAGE_SHORT_SIZE <= DEFAULT_SHORT_SIDE:
			return 2

		RESIZE_SCALE = DEFAULT_SHORT_SIDE / IMAGE_SHORT_SIZE

		NEW_WIDTH  = int(ORIGINAL_WIDTH * RESIZE_SCALE)
		NEW_HEIGHT = int(ORIGINAL_HEIGHT * RESIZE_SCALE)

		HAS_ANIMATION = False

		try:
			IS_ANIMATED_GIF = IMAGE_FILE.is_animated

		except AttributeError:
			IS_ANIMATED_GIF = False
		
		if IS_ANIMATED_GIF:
			FRAMES = []
			DURATIONS = []

			for FRAME_INDEX in range(IMAGE_FILE.n_frames):
				IMAGE_FILE.seek(FRAME_INDEX)

				RESIZED_FRAME = IMAGE_FILE.copy().resize((NEW_WIDTH, NEW_HEIGHT), Image.LANCZOS)
				FRAMES.append(RESIZED_FRAME)

				try:
					DURATION = IMAGE_FILE.info.get('duration', 100)
					DURATIONS.append(DURATION)
				except:
					DURATIONS.append(100)

			FRAMES[0].save( OUTPUT_PATH, save_all=True, append_images=FRAMES[1:], duration=DURATIONS, loop=IMAGE_FILE.info.get('loop', 0), optimize=False)
		else:
			IMAGE_CONV = IMAGE_FILE.resize((NEW_WIDTH, NEW_HEIGHT), Image.LANCZOS)
			IMAGE_CONV.save(OUTPUT_PATH)
		return 1

	except Exception as e:
		return 3
def ConvertVideoWithFFMPEG(FILE_PATH, OUTPUT_PATH):
	try:
		# Probe video untuk mendapatkan informasi
		PROBE_VIDEO = ffmpeg.probe(str(FILE_PATH))
		VIDEO_STREAM = None
		
		# Cari stream video
		for STREAM in PROBE_VIDEO['streams']:
			if STREAM['codec_type'] == 'video':
				VIDEO_STREAM = STREAM
				break
		
		if VIDEO_STREAM is None:
			print("      [ERROR] No video stream found")
			return 3
		
		ORIGINAL_WIDTH = int(VIDEO_STREAM['width'])
		ORIGINAL_HEIGHT = int(VIDEO_STREAM['height'])
		VIDEO_SHORT_SIDE = min(ORIGINAL_WIDTH, ORIGINAL_HEIGHT)
		
		# Cek apakah sudah standard
		if VIDEO_SHORT_SIDE <= DEFAULT_SHORT_SIDE:
			print("      [I] %sx%s - STANDARD" % (ORIGINAL_WIDTH, ORIGINAL_HEIGHT))
			return 2
		
		# Hitung skala resize
		RESIZE_SCALE = DEFAULT_SHORT_SIDE / VIDEO_SHORT_SIDE
		NEW_WIDTH = int(ORIGINAL_WIDTH * RESIZE_SCALE)
		NEW_HEIGHT = int(ORIGINAL_HEIGHT * RESIZE_SCALE)
		
		# Pastikan dimensi genap (requirement untuk codec video)
		NEW_WIDTH = NEW_WIDTH // 2 * 2
		NEW_HEIGHT = NEW_HEIGHT // 2 * 2
		
		print("      [I] %sx%s - %sx%s" % (ORIGINAL_WIDTH, ORIGINAL_HEIGHT, NEW_WIDTH, NEW_HEIGHT))
		
		# Proses resize video
		(
			ffmpeg
			.input(str(FILE_PATH))
			.filter("scale", NEW_WIDTH, NEW_HEIGHT)
			.output(
				str(OUTPUT_PATH),
				vcodec="libx264",
				acodec="copy",
				crf=18,
				preset="slow"
			)
			.run(overwrite_output=True, quiet=True)
		)
		
		return 1
		
	except ffmpeg.Error as e:
		print(f"      [ERROR] FFmpeg error: {e.stderr.decode() if e.stderr else 'Unknown error'}")
		return 3
	except Exception as e:
		print(f"      [ERROR] {str(e)}")
		return 3

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
					
					ConvertPhotoWithPillow(TEMP_FILE, '%s.png' % FOLDER / PHOTO_COUNT)
					print('%.32s --- %.32s --- %.32s.png' % (FILE, TEMP_FILE, PHOTO_COUNT))
					PHOTO_COUNT += 1

				else:
					ConvertPhotoWithPillow(FILE, '%s.png' % FOLDER / PHOTO_COUNT)
					print('%.32s --- %.32s.png' % (FILE, PHOTO_COUNT))
					PHOTO_COUNT += 1

			elif FILE.suffix.lower() in SCAN_PHOTO_FORMAT and FILE.suffix.lower() == '.gif':
				if FILE.stem.isdigit():
					TEMP_FILE = FILE.parent / ('TEMP_%s' % FILE.name)
					os.rename(FILE, TEMP_FILE)
					
					ConvertPhotoWithPillow(TEMP_FILE, '%s.gif' % FOLDER / GIF_COUNT)
					print('%.32s --- %.32s --- %.32s.gif' % (FILE, TEMP_FILE, GIF_COUNT))
					GIF_COUNT += 1

				else:
					ConvertPhotoWithPillow(FILE, '%s.gif' % FOLDER / GIF_COUNT)
					print('%.32s --- %.32s.gif' % (FILE, GIF_COUNT))
					GIF_COUNT += 1

			elif FILE.suffix.lower() in SCAN_VIDEO_FORMAT:
				if FILE.stem.isdigit():
					TEMP_FILE = FILE.parent / ('TEMP_%s' % FILE.name)
					
					ConvertVideoWithFFMPEG(FILE, '%s.mp4' % FOLDER / VIDEO_COUNT)
					print('%.32s --- %.32s --- %.32s.mp4' % (FILE, TEMP_FILE, VIDEO_COUNT))
					VIDEO_COUNT += 1

				else:
					ConvertVideoWithFFMPEG(FILE, '%s.mp4' % FOLDER / VIDEO_COUNT)
					print('%.32s --- %.32s.mp4' % (FILE, VIDEO_COUNT))
					VIDEO_COUNT += 1

# Main Program

def Main():
	ConvertionRenameLogic(ScanDirectoryWithPathlib(DEFAULT_WORKING_DIRECTORY))

if __name__ == '__main__':
	Main()