import argparse
import os
import subprocess
import sys

sys.stdout.reconfigure(line_buffering=True)

def main(mpd_path, filename, output_dir, rep_idx):
    # Define the output file path
    output_mp4 = os.path.join(output_dir, filename)
    
    # Print for debugging
    print(f"Output file: {output_mp4}")
    print(f"MPD path: {mpd_path}")
    
    command = [
        "ffmpeg",
        "-i", mpd_path,   # Input MPD file
        "-map", f"0:v:{rep_idx}",     # Map the third video stream (0-based index)
        "-map", "0:a:0",     # Map the first audio stream
        "-c", "copy",        # Copy the streams without re-encoding
        output_mp4         # Output file
    ]

    # Let ffmpeg use the same stdout and stderr as the parent process
    subprocess.run(command, check=True)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video builder script using ffmpeg.")
    parser.add_argument("--mpd_path", default="./index.mpd", help="(required) Path for input mpd file to make video from.")
    parser.add_argument("--filename", default="output.mp4", help="Output video file name.")
    parser.add_argument("--output_dir", default=".", help="output folder for mpd file")
    parser.add_argument("--rep_idx", type=int, default=0, help="Representation index for the target resolution video. The mapping is following: 0: 1080, 1: 720, 2: 360")
    
    args = parser.parse_args()
    
    main(args.mpd_path, args.filename, args.output_dir, args.rep_idx)