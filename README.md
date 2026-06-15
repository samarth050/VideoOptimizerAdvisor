# Video Optimizer Advisor

A Windows GUI application built in Python to analyze a video file and suggest size-reduction strategies with minimal quality loss.

## Features

- Browse and select a video file from the local system
- Analyze video metadata such as:
  - file size
  - resolution
  - duration
  - frame rate
  - codec / encoding details
  - estimated bitrate
- Provide practical optimization advice for reducing file size while preserving visual quality
- Suggest free tools such as FFmpeg, HandBrake, and VLC, along with recommended settings

## Requirements

Python 3.10 or newer

Install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run the application

```powershell
.\.venv\Scripts\python.exe main.py
```

## Notes

- The app uses FFmpeg binaries from `D:\Tools\ffmpeg\bin` for accurate metadata analysis.
- For best compression results, use FFmpeg or HandBrake with CRF-based encoding and moderate presets.

## License

This project is provided for educational and personal use.
