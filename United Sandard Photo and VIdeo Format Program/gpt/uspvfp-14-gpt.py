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

def CheckImageFormat(FILE_PATH):
	"""Cek apakah gambar sudah sesuai format (sisi pendek <= 720px)"""
	try:
		IMAGE_FILE = Image.open(FILE_PATH)
		ORIGINAL_WIDTH, ORIGINAL_HEIGHT = IMAGE_FILE.size
		IMAGE_SHORT_SIZE = min(ORIGINAL_WIDTH, ORIGINAL_HEIGHT)
		IMAGE_FILE.close()
		return IMAGE_SHORT_SIZE <= TARGET_SHORT_SIDE
	except:
		return False

def CheckVideoFormat(FILE_PATH):
	"""Cek apakah video sudah sesuai format (sisi pendek <= 720px)"""
	try:
		PROBE_VIDEO = ffmpeg.probe(str(FILE_PATH))
		VIDEO_STREAM = None
		
		for STREAM in PROBE_VIDEO['streams']:
			if STREAM['codec_type'] == 'video':
				VIDEO_STREAM = STREAM
				break
		
		if VIDEO_STREAM is None:
			return False
		
		ORIGINAL_WIDTH = int(VIDEO_STREAM['width'])
		ORIGINAL_HEIGHT = int(VIDEO_STREAM['height'])
		VIDEO_SHORT_SIDE = min(ORIGINAL_WIDTH, ORIGINAL_HEIGHT)
		
		return VIDEO_SHORT_SIDE <= TARGET_SHORT_SIDE
	except:
		return False

def RevalidateExistingFiles(FOLDER_PATH, EXTENSION):
	"""Periksa dan rekonversi file existing yang tidak sesuai format"""
	# Cari semua file dengan format numeric
	ALL_FILES = []
	
	for FILE in FOLDER_PATH.glob(f'*{EXTENSION}'):
		if FILE.stem.isdigit():
			ALL_FILES.append(FILE)
	
	if not ALL_FILES:
		return 0
	
	# Sort berdasarkan nomor
	ALL_FILES.sort(key=lambda x: int(x.stem))
	
	# Periksa dan konversi file yang tidak valid
	for FILE in ALL_FILES:
		FILE_NUMBER = int(FILE.stem)
		
		# Cek apakah file sudah sesuai format
		if EXTENSION in {'.png', '.gif'}:
			IS_VALID = CheckImageFormat(FILE)
		elif EXTENSION == '.mp4':
			IS_VALID = CheckVideoFormat(FILE)
		else:
			IS_VALID = False
		
		if not IS_VALID:
			print("   [REVALIDATE] %s" % FILE.name)
			
			# Buat nama temporary
			TEMP_NAME = 'temp_%s%s' % (FILE_NUMBER, EXTENSION)
			TEMP_PATH = FILE.parent / TEMP_NAME
			
			# Konversi ke file temporary
			if EXTENSION in {'.png', '.gif'}:
				RESULT = ConvertImageWithPillow(FILE, TEMP_PATH)
			elif EXTENSION == '.mp4':
				RESULT = ConvertVideoWithFFMPEG(FILE, TEMP_PATH)
			else:
				RESULT = 3
			
			# Jika berhasil, hapus file asli dan rename temporary
			if RESULT == 1:
				FILE.unlink()  # Hapus file asli
				TEMP_PATH.rename(FILE)  # Rename temp ke nama asli
				print("   [REVALIDATE OK] %s" % FILE.name)
			elif RESULT == 2:
				# File skip, tapi ini seharusnya tidak terjadi karena sudah dicek tidak valid
				if TEMP_PATH.exists():
					TEMP_PATH.unlink()
				print("   [REVALIDATE SKIP] %s" % FILE.name)
			else:
				# Error, hapus temp file
				if TEMP_PATH.exists():
					TEMP_PATH.unlink()
				print("   [REVALIDATE ERROR] %s" % FILE.name)
	
	# Return counter tertinggi yang ada
	if ALL_FILES:
		return max(int(f.stem) for f in ALL_FILES)
	return 0
	try:
		IMAGE_FILE                      = Image.open(FILE_PATH)

		ORIGINAL_WIDTH, ORIGINAL_HEIGHT = IMAGE_FILE.size
		IMAGE_SHORT_SIZE                = min(ORIGINAL_WIDTH, ORIGINAL_HEIGHT)

		if IMAGE_SHORT_SIZE <= TARGET_SHORT_SIDE:
			return 2

		RESIZE_SCALE = TARGET_SHORT_SIDE / IMAGE_SHORT_SIZE

		NEW_WIDTH  = int(ORIGINAL_WIDTH * RESIZE_SCALE)
		NEW_HEIGHT = int(ORIGINAL_HEIGHT * RESIZE_SCALE)

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

			FRAMES[0].save(OUTPUT_PATH, save_all=True, append_images=FRAMES[1:], duration=DURATIONS, loop=IMAGE_FILE.info.get('loop', 0), optimize=False)
		else:
			IMAGE_CONV = IMAGE_FILE.resize((NEW_WIDTH, NEW_HEIGHT), Image.LANCZOS)
			IMAGE_CONV.save(OUTPUT_PATH)
		return 1

	except Exception as e:
		return 3

def ConvertVideoWithFFMPEG(FILE_PATH, OUTPUT_PATH):
	try:
		PROBE_VIDEO = ffmpeg.probe(str(FILE_PATH))
		VIDEO_STREAM = None
		
		for STREAM in PROBE_VIDEO['streams']:
			if STREAM['codec_type'] == 'video':
				VIDEO_STREAM = STREAM
				break
		
		if VIDEO_STREAM is None:
			return 3
		
		ORIGINAL_WIDTH = int(VIDEO_STREAM['width'])
		ORIGINAL_HEIGHT = int(VIDEO_STREAM['height'])
		VIDEO_SHORT_SIDE = min(ORIGINAL_WIDTH, ORIGINAL_HEIGHT)
		
		if VIDEO_SHORT_SIDE <= TARGET_SHORT_SIDE:
			return 2
		
		RESIZE_SCALE = TARGET_SHORT_SIDE / VIDEO_SHORT_SIDE
		NEW_WIDTH = int(ORIGINAL_WIDTH * RESIZE_SCALE)
		NEW_HEIGHT = int(ORIGINAL_HEIGHT * RESIZE_SCALE)
		
		NEW_WIDTH = NEW_WIDTH // 2 * 2
		NEW_HEIGHT = NEW_HEIGHT // 2 * 2
		
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
		
	except Exception as e:
		return 3

def Main():
	CONVERTION_SUCCESS = 0
	CONVERTION_SKIP    = 0
	CONVERTION_ERROR   = 0

	for FOLDER_PATH, FILE_LIST in ScanDiretoryWithPathlib(WORKING_DIRECTORY).items():
		print("[+] %s" % FOLDER_PATH)
		print("[*] Revalidating existing files...")
		
		# Revalidasi file existing untuk setiap format
		COUNTER_PNG = RevalidateExistingFiles(FOLDER_PATH, '.png')
		COUNTER_GIF = RevalidateExistingFiles(FOLDER_PATH, '.gif')
		COUNTER_MP4 = RevalidateExistingFiles(FOLDER_PATH, '.mp4')
		
		print("[*] Starting conversion... (PNG:%s, GIF:%s, MP4:%s)" % (COUNTER_PNG, COUNTER_GIF, COUNTER_MP4))

		for FILE in FILE_LIST:
			FILE_EXTENSION = FILE.suffix.lower()
			print("   [-] %s" % FILE)

			if FILE_EXTENSION in SCAN_PHOTO_FORMAT:
				# Tentukan format output dan counter
				if FILE_EXTENSION == '.gif':
					COUNTER_GIF += 1
					OUTPUT_NAME = '%s.gif' % COUNTER_GIF
				else:
					COUNTER_PNG += 1
					OUTPUT_NAME = '%s.png' % COUNTER_PNG

				OUTPUT_PATH = FILE.parent / OUTPUT_NAME
				RESULT_CODE = ConvertImageWithPillow(FILE, OUTPUT_PATH)

				if RESULT_CODE == 1:
					CONVERTION_SUCCESS += 1

				elif RESULT_CODE == 2:
					CONVERTION_SKIP += 1

				elif RESULT_CODE == 3:
					CONVERTION_ERROR += 1

			elif FILE_EXTENSION in SCAN_VIDEO_FORMAT:
				COUNTER_MP4 += 1
				OUTPUT_NAME = '%s.mp4' % COUNTER_MP4
				OUTPUT_PATH = FILE.parent / OUTPUT_NAME
				
				RESULT_CODE = ConvertVideoWithFFMPEG(FILE, OUTPUT_PATH)
				
				if RESULT_CODE == 1:
					CONVERTION_SUCCESS += 1
				
				elif RESULT_CODE == 2:
					CONVERTION_SKIP += 1
				
				elif RESULT_CODE == 3:
					CONVERTION_ERROR += 1

	print("%s-%s-%s" % (CONVERTION_SUCCESS, CONVERTION_SKIP, CONVERTION_ERROR))

if __name__ == '__main__':
	Main()