import ffmpeg
from PIL import Image
import pathlib
import re

WORKING_DIRECTORY   = pathlib.Path('.')

SCAN_PHOTO_FORMAT   = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.gif'}
SCAN_VIDEO_FORMAT   = {'.mp4', '.mkv', '.mov', '.avi', '.flv', '.wmv', '.webm', '.ts'}

OUTPUT_PHOTO_FORMAT = {'.png', '.gif'}
OUTPUT_VIDEO_FORMAT = {'.mp4'}

TARGET_SHORT_SIDE   = 720

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
	try:
		IMAGE_FILE                      = Image.open(FILE_PATH)

		ORIGINAL_WIDTH, ORIGINAL_HEIGHT = IMAGE_FILE.size
		IMAGE_SHORT_SIZE                = min(ORIGINAL_WIDTH, ORIGINAL_HEIGHT)

		if IMAGE_SHORT_SIZE <= TARGET_SHORT_SIDE:
			return 2

		RESIZE_SCALE = TARGET_SHORT_SIDE / IMAGE_SHORT_SIZE

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
	pass

def Main():
	CONVERTION_SUCCESS = 0
	CONVERTION_SKIP    = 0
	CONVERTION_ERROR   = 0

	for FOLDER_PATH, FILE_LIST in ScanDiretoryWithPathlib(WORKING_DIRECTORY).items():
		print("[+] %s" % FOLDER_PATH)

		for FILE in FILE_LIST:
			FILE_EXTENSION = FILE.suffix.lower()
			print("   [-] %s" % FILE)

			if FILE_EXTENSION in SCAN_PHOTO_FORMAT:
				if FILE_EXTENSION == '.gif':
					OUTPUT_NAME = '%s-conv.gif' % FILE.stem
				else:
					OUTPUT_NAME = '%s-conv.png' % FILE.stem

				OUTPUT_PATH = FILE.parent / OUTPUT_NAME
				RESULT_CODE = ConvertImageWithPillow(FILE, OUTPUT_PATH)

				if RESULT_CODE == 1:
					CONVERTION_SUCCESS = CONVERTION_SUCCESS + 1

				elif RESULT_CODE == 2:
					CONVERTION_SKIP = CONVERTION_SKIP + 1

				elif RESULT_CODE == 3:
					CONVERTION_ERROR = CONVERTION_ERROR + 1

			elif FILE_EXTENSION in SCAN_VIDEO_FORMAT:
				pass

	print("%s-%s-%s" % (CONVERTION_SUCCESS, CONVERTION_SKIP, CONVERTION_ERROR))

if __name__ == '__main__':
	Main()