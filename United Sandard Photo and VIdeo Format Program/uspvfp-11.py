import ffmpeg as ffm

VIDEO_PATH          = input("Video : ")

PROBE_VIDEO         = ffm.probe(VIDEO_PATH)
VIDEO_STREAM        = None
STANDARD_SHORT_SIDE = 720

for STREAM in PROBE_VIDEO['streams']:
	if STREAM['codec_type'] == 'video':
		VIDEO_STREAM = STREAM
		break

ORIGINAL_WIDTH      = int(VIDEO_STREAM['width'])
ORIGINAL_HEIGHT     = int(VIDEO_STREAM['height'])
VIDEO_SHORT_SIDE    = min(ORIGINAL_WIDTH, ORIGINAL_HEIGHT)
RESIZE_SCALE        = STANDARD_SHORT_SIDE / VIDEO_SHORT_SIDE
NEW_WIDTH           = int(ORIGINAL_WIDTH  * RESIZE_SCALE)
NEW_HEIGHT          = int(ORIGINAL_HEIGHT * RESIZE_SCALE)

NEW_WIDTH           = NEW_WIDTH  // 2 * 2
NEW_HEIGHT          = NEW_HEIGHT // 2 * 2

OUTPUT_PATH         = "resized.mp4"

(
    ffm
    .input(VIDEO_PATH)
    .filter("scale", NEW_WIDTH, NEW_HEIGHT)
    .output(
        OUTPUT_PATH,
        vcodec="libx264",
        acodec="copy",
        crf=18,
        preset="slow"
    )
    .run(overwrite_output=True)
)

print("ORIGINAL : %s %s" % (ORIGINAL_WIDTH, ORIGINAL_HEIGHT))
print("RESIZED  : %s %s" % (NEW_WIDTH, NEW_HEIGHT))
print("OUTPUT   : %s" % OUTPUT_PATH)