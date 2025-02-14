# ThreeSixtyDownloader

ThreeSixtyDownloader is a set of tools useful for downloading videos from `360tka.sk`. 

## Requirements
- Python 3.9
- ffmpeg 7.1
- chromium

## Setup
Make sure you have Pyhton and ffmpeg installed. Run `pip install -r requirements.txt` to install all required python packages. After that, if you didnt have chromium installed, run `playwright install`. After this you are ready to use the `ThreeSixtyDownloader` tools. 

## Workflow
First you need to download MPD file for a specific 360tka video url. You just the web page with the video you wanna download and copy the url from the browser. Then run `mpd_builder.py` script with parameter `url`. Example:
```
python mpd_builder --url http://url_to_your_video
```
At this point, the mpd file should be downloaded and stored to the location you specified (default is the folder where you are running the script from). See the possible script arguments with `python mpd_builder.py --helm`.

Second step is to run `video_builder.py` script, which uses ffmpeg to create a video out from that mpd file. See the possible script arguments with `python video_builder.py --helm`

Alternatively, you can just directly call ffmpeg without python script, with this command:
```
ffmpeg -i "index.mpd" -map 0:v:2 -map 0:a:0 -c copy output.mp4
```

Where 0:v:2 is a mapping to a video representation with the mpd file and 0:a:0 is the audio representation. There is only one audio representation. For video representations, there are 3 options:
- 0:v:0 is for 1080 resolution
- 0:v:1 is for 720 resolution
- 0:v:2 is for 360 resolution