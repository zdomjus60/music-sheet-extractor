# Music Sheet Extractor

This script extracts sheet music pages from a video file and compiles them into a printable PDF document.

It works by detecting scene changes in the video, which usually correspond to page turns. Each new page is saved as an image, cropped to remove black borders, and then all pages are combined into a single PDF file, with two pages per A4 sheet.

## Installation

1.  Clone the repository:
    ```bash
    git clone <your-repository-url>
    ```
2.  Navigate to the project directory:
    ```bash
    cd music_sheet_extractor
    ```
3.  Install the required dependencies using pip:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Create a file named `video_list.txt` in the root of the project.
2.  Add the full paths to your video files in `video_list.txt`, one video per line.
3.  Run the script:
    ```bash
    python3 extractor.py
    ```
4.  The script will generate a `_score.pdf` file for each video processed.

### Optional: Download videos from YouTube

The script can also download videos from YouTube using `yt-dlp`.

1.  Install `yt-dlp`:
    ```bash
    pip install yt-dlp
    ```
2.  Download a video:
    ```bash
    yt-dlp <video-url>
    ```
3.  Add the downloaded video file name to `video_list.txt` and run the extractor as described above.
