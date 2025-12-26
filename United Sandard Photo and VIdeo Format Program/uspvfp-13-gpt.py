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
		IMAGE_FILE = Image.open(FILE_PATH)
		
		ORIGINAL_WIDTH, ORIGINAL_HEIGHT = IMAGE_FILE.size
		IMAGE_SHORT_SIZE = min(ORIGINAL_WIDTH, ORIGINAL_HEIGHT)
		
		# Cek apakah sudah standard
		if IMAGE_SHORT_SIZE <= TARGET_SHORT_SIDE:
			print("      [SKIP] Already standard size")
			return "SKIP"
		
		# Hitung skala resize
		RESIZE_SCALE = TARGET_SHORT_SIDE / IMAGE_SHORT_SIZE
		
		NEW_WIDTH  = int(ORIGINAL_WIDTH * RESIZE_SCALE)
		NEW_HEIGHT = int(ORIGINAL_HEIGHT * RESIZE_SCALE)
		
		print(f"      [RESIZE] {ORIGINAL_WIDTH}x{ORIGINAL_HEIGHT} -> {NEW_WIDTH}x{NEW_HEIGHT}")
		
		# Cek apakah file adalah GIF animasi
		IS_ANIMATED_GIF = False
		try:
			IS_ANIMATED_GIF = IMAGE_FILE.is_animated
		except AttributeError:
			IS_ANIMATED_GIF = False
		
		if IS_ANIMATED_GIF:
			# Proses GIF animasi
			print("      [GIF] Processing animated GIF")
			FRAMES = []
			DURATIONS = []
			
			for FRAME_INDEX in range(IMAGE_FILE.n_frames):
				IMAGE_FILE.seek(FRAME_INDEX)
				
				# Resize frame
				RESIZED_FRAME = IMAGE_FILE.copy().resize((NEW_WIDTH, NEW_HEIGHT), Image.LANCZOS)
				FRAMES.append(RESIZED_FRAME)
				
				# Simpan durasi frame
				try:
					DURATION = IMAGE_FILE.info.get('duration', 100)
					DURATIONS.append(DURATION)
				except:
					DURATIONS.append(100)
			
			# Simpan GIF animasi
			FRAMES[0].save(
				OUTPUT_PATH,
				save_all=True,
				append_images=FRAMES[1:],
				duration=DURATIONS,
				loop=IMAGE_FILE.info.get('loop', 0),
				optimize=False
			)
		else:
			# Proses gambar biasa atau GIF statis
			IMAGE_CONV = IMAGE_FILE.resize((NEW_WIDTH, NEW_HEIGHT), Image.LANCZOS)
			IMAGE_CONV.save(OUTPUT_PATH)
		
		return "SUCCESS"
		
	except Exception as e:
		print(f"      [ERROR] {str(e)}")
		return "ERROR"

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
		if VIDEO_SHORT_SIDE <= TARGET_SHORT_SIDE:
			print("      [I] %sx%s - STANDARD" % (ORIGINAL_WIDTH, ORIGINAL_HEIGHT))
			return 2
		
		# Hitung skala resize
		RESIZE_SCALE = TARGET_SHORT_SIDE / VIDEO_SHORT_SIDE
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

def Main():
	CONVERTION_SUCCESS = 0
	CONVERTION_SKIP    = 0
	CONVERTION_ERROR   = 0

	for FOLDER_PATH, FILE_LIST in ScanDiretoryWithPathlib(WORKING_DIRECTORY).items():
		print("[+] %s" % FOLDER_PATH)

		for FILE in FILE_LIST:
			FILE_EXTENSION = FILE.suffix.lower()
			print("   [-] %s" % FILE.name)

			if FILE_EXTENSION in SCAN_PHOTO_FORMAT:
				# Buat nama output file (GIF tetap jadi GIF, lainnya jadi PNG)
				if FILE_EXTENSION == '.gif':
					OUTPUT_NAME = FILE.stem + '-conv.gif'
				else:
					OUTPUT_NAME = FILE.stem + '-conv.png'
				
				OUTPUT_PATH = FILE.parent / OUTPUT_NAME
				
				RESULT = ConvertImageWithPillow(FILE, OUTPUT_PATH)
				
				if RESULT == "SUCCESS":
					CONVERTION_SUCCESS += 1
				elif RESULT == "SKIP":
					CONVERTION_SKIP += 1
				elif RESULT == "ERROR":
					CONVERTION_ERROR += 1

			elif FILE_EXTENSION in SCAN_VIDEO_FORMAT:
				OUTPUT_NAME = '%s-conv.mp4' % FILE.stem
				OUTPUT_PATH = FILE.parent / OUTPUT_NAME
				
				RESULT_CODE = ConvertVideoWithFFMPEG(FILE, OUTPUT_PATH)
				
				if RESULT_CODE == 1:
					CONVERTION_SUCCESS += 1
					print("   [+]")
				
				elif RESULT_CODE == 2:
					CONVERTION_SKIP += 1
					print("   [-]")
				
				elif RESULT_CODE == 3:
					CONVERTION_ERROR += 1
					print("   [X]")

	print()
	print("=" * 50)
	print(f"Conversion Summary:")
	print(f"  Success: {CONVERTION_SUCCESS}")
	print(f"  Skipped: {CONVERTION_SKIP}")
	print(f"  Errors:  {CONVERTION_ERROR}")
	print("=" * 50)

if __name__ == '__main__':
	Main()