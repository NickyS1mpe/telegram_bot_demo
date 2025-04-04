import os

import ffmpeg


def convert_mp4_to_avi(input_file, output_file):
    (
        ffmpeg
        .input(input_file)
        .output(
            output_file,
            vcodec='mjpeg',  # MJPEG encoder
            # qscale_v=3,
            an=None,
            vf='scale=240:240',  # Resize
            r=15,
            # acodec='pcm_s16le'
        )
        .run()
    )
    print(f"Conversion completed: {output_file}")

    # delete the input file
    if os.path.exists(input_file):
        os.remove(input_file)

# convert_mp4_to_avi("video/demo.MP4", "video/output.avi")
