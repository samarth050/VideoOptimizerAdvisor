import json
import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2

FFMPEG_BIN = r"D:\Tools\ffmpeg\bin"


class VideoOptimizerAdvisorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Video Optimizer Advisor")
        self.root.geometry("1080x860")
        self.root.minsize(1020, 820)

        self.style = ttk.Style(root)
        self.style.theme_use("clam")

        self._build_ui()

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill="both", expand=True)

        title = ttk.Label(main, text="Video Optimizer Advisor", font=("Segoe UI", 18, "bold"))
        title.pack(anchor="w", pady=(0, 8))

        subtitle = ttk.Label(
            main,
            text="Pick a single video file or a folder of clips to inspect characteristics, estimate combined size, and receive quality-preserving optimization suggestions.",
            wraplength=980,
            justify="left",
            font=("Segoe UI", 10),
        )
        subtitle.pack(anchor="w", pady=(0, 12))

        pick_frame = ttk.Frame(main)
        pick_frame.pack(fill="x", pady=(0, 10))

        self.path_var = tk.StringVar(value="")
        self.path_entry = ttk.Entry(pick_frame, textvariable=self.path_var, width=90)
        self.path_entry.pack(side="left", fill="x", expand=True)

        browse_btn = ttk.Button(pick_frame, text="Browse Video…", command=self.choose_file)
        browse_btn.pack(side="left", padx=(8, 0))

        folder_btn = ttk.Button(pick_frame, text="Browse Folder…", command=self.choose_folder)
        folder_btn.pack(side="left", padx=(8, 0))

        button_row = ttk.Frame(main)
        button_row.pack(anchor="w", pady=(0, 10))

        self.analyze_btn = ttk.Button(button_row, text="Analyze Video", command=self.analyze_video)
        self.analyze_btn.pack(side="left")

        self.analyze_folder_btn = ttk.Button(button_row, text="Analyze Folder", command=self.analyze_folder)
        self.analyze_folder_btn.pack(side="left", padx=(8, 0))

        save_btn = ttk.Button(button_row, text="Save Report", command=self.save_report)
        save_btn.pack(side="left", padx=(8, 0))

        reset_btn = ttk.Button(button_row, text="Reset", command=self.reset_view)
        reset_btn.pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value="Ready. Select a video file to begin.")
        status = ttk.Label(main, textvariable=self.status_var, foreground="#1f5fbf", font=("Segoe UI", 10))
        status.pack(anchor="w", pady=(0, 8))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_label = ttk.Label(main, text="", font=("Segoe UI", 9))
        self.progress_label.pack(anchor="w", pady=(0, 2))
        self.progress_bar = ttk.Progressbar(main, variable=self.progress_var, mode="determinate", length=420)
        self.progress_bar.pack(anchor="w", fill="x", pady=(0, 8))
        self.progress_bar.pack_forget()
        self.progress_label.pack_forget()

        notebook = ttk.Notebook(main)
        notebook.pack(fill="both", expand=True)

        self.summary_text = tk.Text(notebook, height=14, wrap="word", font=("Consolas", 10))
        self.summary_scroll = ttk.Scrollbar(self.summary_text, orient="vertical", command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=self.summary_scroll.set)
        self.summary_text.pack(fill="both", expand=True)

        overview = ttk.Frame(notebook)
        self.recommend_text = tk.Text(overview, wrap="word", font=("Segoe UI", 10))
        self.recommend_scroll = ttk.Scrollbar(self.recommend_text, orient="vertical", command=self.recommend_text.yview)
        self.recommend_text.configure(yscrollcommand=self.recommend_scroll.set)
        self.recommend_text.pack(fill="both", expand=True)

        tools = ttk.Frame(notebook)
        self.tools_text = tk.Text(tools, wrap="word", font=("Segoe UI", 10))
        self.tools_scroll = ttk.Scrollbar(self.tools_text, orient="vertical", command=self.tools_text.yview)
        self.tools_text.configure(yscrollcommand=self.tools_scroll.set)
        self.tools_text.pack(fill="both", expand=True)

        notebook.add(self.summary_text, text="Analysis Summary")
        notebook.add(overview, text="Optimization Advice")
        notebook.add(tools, text="Free Tools & Configs")

        self.summary_text.insert("1.0", "Select a video file to generate the analysis report.\n")
        self.recommend_text.insert("1.0", "Suggestions will appear here after analysis.\n")
        self.tools_text.insert("1.0", "Recommended free tools and preset settings will appear here after analysis.\n")
        self.last_report_text = ""
        self.last_advice_text = ""
        self.last_tools_text = ""
        self._update_action_buttons("")

    def choose_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Open video file",
            filetypes=[
                ("Video files", "*.mp4 *.mkv *.mov *.avi *.wmv *.webm *.m4v *.ts *.mts *.mpg *.mpeg"),
                ("All files", "*.*"),
            ],
        )
        if file_path:
            self.path_var.set(file_path)
            self._update_action_buttons(file_path)
            self.status_var.set("File selected. Click Analyze Video to inspect it.")

    def choose_folder(self) -> None:
        folder_path = filedialog.askdirectory(title="Choose a folder of videos")
        if folder_path:
            self.path_var.set(folder_path)
            self._update_action_buttons(folder_path)
            self.status_var.set("Folder selected. Click Analyze Folder for combined recommendations.")

    def _update_action_buttons(self, path_value: str) -> None:
        is_file = os.path.isfile(path_value)
        is_folder = os.path.isdir(path_value)

        self.analyze_btn.state(["!disabled"] if is_file else ["disabled"])
        self.analyze_folder_btn.state(["!disabled"] if is_folder else ["disabled"])

    def analyze_video(self) -> None:
        file_path = self.path_var.get().strip()
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Missing file", "Please choose a valid video file before analyzing.")
            return

        try:
            self.status_var.set("Analyzing video…")
            self.root.update_idletasks()
            info = self._collect_video_info(file_path)
            self._render_report(file_path, info)
            self.status_var.set("Analysis complete. Review the recommendations below.")
        except Exception as exc:
            messagebox.showerror("Analysis failed", f"Unable to analyze the video file.\n\n{exc}")
            self.status_var.set("Analysis failed. Please try another file.")

    def analyze_folder(self) -> None:
        folder_path = self.path_var.get().strip()
        if not folder_path or not os.path.isdir(folder_path):
            messagebox.showerror("Missing folder", "Please choose a valid folder containing video files before analyzing it.")
            return

        try:
            video_files = self._find_video_files(folder_path)
            if not video_files:
                messagebox.showerror("No video files", "No supported video files were found in the selected folder.")
                return

            self._show_progress(True, len(video_files))
            self.status_var.set("Analyzing folder of videos…")
            threading.Thread(target=self._run_folder_analysis, args=(folder_path, video_files), daemon=True).start()
        except Exception as exc:
            self._show_progress(False)
            messagebox.showerror("Folder analysis failed", f"Unable to analyze the folder.\n\n{exc}")
            self.status_var.set("Folder analysis failed. Please try another folder.")

    def _run_folder_analysis(self, folder_path: str, video_files: list[str]) -> None:
        try:
            info = self._collect_folder_info(folder_path, video_files, progress_callback=self._update_progress)
            self.root.after(0, lambda: self._finish_folder_analysis(folder_path, info, video_files))
        except Exception as exc:
            self.root.after(0, lambda: self._handle_folder_error(exc))

    def _show_progress(self, visible: bool, total: int = 0) -> None:
        if visible:
            self.progress_bar['maximum'] = max(total, 1)
            self.progress_var.set(0)
            self.progress_label.config(text='Scanning videos…')
            self.progress_bar.pack()
            self.progress_label.pack()
        else:
            self.progress_bar.pack_forget()
            self.progress_label.pack_forget()
            self.progress_var.set(0)

    def _update_progress(self, completed: int, file_path: str) -> None:
        self.root.after(0, lambda: self._apply_progress(completed, file_path))

    def _apply_progress(self, completed: int, file_path: str) -> None:
        self.progress_var.set(completed)
        self.progress_label.config(text=f'Processed {completed} of {int(self.progress_bar["maximum"])} files — {os.path.basename(file_path)}')
        self.root.update_idletasks()

    def _finish_folder_analysis(self, folder_path: str, info: dict, video_files: list[str]) -> None:
        self._show_progress(False)
        self._render_folder_report(folder_path, info, video_files)
        self.status_var.set("Folder analysis complete. Review the combined recommendations below.")

    def _handle_folder_error(self, exc: Exception) -> None:
        self._show_progress(False)
        messagebox.showerror("Folder analysis failed", f"Unable to analyze the folder.\n\n{exc}")
        self.status_var.set("Folder analysis failed. Please try another folder.")

    def _find_video_files(self, folder_path: str) -> list[str]:
        extensions = (".mp4", ".mkv", ".mov", ".avi", ".wmv", ".webm", ".m4v", ".ts", ".mts", ".mpg", ".mpeg")
        return [
            os.path.join(root, file_name)
            for root, _, files in os.walk(folder_path)
            for file_name in files
            if os.path.splitext(file_name)[1].lower() in extensions
        ]

    def _collect_folder_info(self, folder_path: str, video_files: list[str], progress_callback=None) -> dict:
        total_bytes = 0
        total_duration = 0.0
        total_weighted_fps = 0.0
        codec_counts = {}
        resolution_counts = {}
        max_width = 0
        max_height = 0

        for index, file_path in enumerate(video_files, start=1):
            info = self._collect_video_info(file_path)
            total_bytes += info["file_size_bytes"]
            total_duration += info["duration"]
            total_weighted_fps += info["fps"] * info["duration"]
            codec_counts[info["codec"]] = codec_counts.get(info["codec"], 0) + 1
            resolution_counts[info["resolution"]] = resolution_counts.get(info["resolution"], 0) + 1
            max_width = max(max_width, info["width"])
            max_height = max(max_height, info["height"])
            if progress_callback is not None:
                progress_callback(index, file_path)

        avg_fps = (total_weighted_fps / total_duration) if total_duration > 0 else 0.0
        dominant_resolution = max(resolution_counts, key=resolution_counts.get) if resolution_counts else "Unknown"
        dominant_codec = max(codec_counts, key=codec_counts.get) if codec_counts else "Unknown"

        return {
            "folder_path": folder_path,
            "video_files": video_files,
            "total_files": len(video_files),
            "total_size_bytes": total_bytes,
            "total_size_display": self._format_file_size(total_bytes),
            "total_duration": total_duration,
            "avg_fps": avg_fps,
            "dominant_resolution": dominant_resolution,
            "dominant_codec": dominant_codec,
            "max_width": max_width,
            "max_height": max_height,
            "recommended_resolution": self._recommended_output_resolution(max_width, max_height),
            "recommended_codec": self._recommended_output_codec(dominant_codec),
            "recommended_fps": self._recommended_output_fps(avg_fps),
            "recommended_preset": self._recommended_preset(total_bytes),
            "recommended_bitrate": self._recommended_bitrate(max_width, max_height),
        }

    def _recommended_output_resolution(self, max_width: int, max_height: int) -> str:
        if max_width >= 3840 or max_height >= 2160:
            return "1920x1080 (recommended for best size/quality balance)"
        if max_width >= 1920 or max_height >= 1080:
            return "1920x1080"
        if max_width >= 1280 or max_height >= 720:
            return "1280x720"
        return f"{max_width}x{max_height}"

    def _recommended_output_codec(self, dominant_codec: str) -> str:
        return "H.265 / HEVC" if dominant_codec not in ("H264", "AVC1", "H.264") else "H.264 / AVC"

    def _recommended_output_fps(self, avg_fps: float) -> str:
        if avg_fps >= 55:
            return "30 fps (best balance for export)"
        if avg_fps >= 35:
            return "30 fps"
        return "Use source frame rate or 24/30 fps"

    def _recommended_preset(self, total_bytes: int) -> str:
        return "Slow" if total_bytes > 1024 * 1024 * 500 else "Medium"

    def _recommended_bitrate(self, max_width: int, max_height: int) -> str:
        pixel_count = max_width * max_height
        if pixel_count >= 3840 * 2160:
            return "12–18 Mbps for 4K output"
        if pixel_count >= 1920 * 1080:
            return "6–10 Mbps for 1080p output"
        return "3–6 Mbps for 720p output"

    def _recommended_output_bitrate_kbps(self, width: int, height: int) -> float:
        pixel_count = width * height
        if pixel_count >= 3840 * 2160:
            return 14000.0
        if pixel_count >= 1920 * 1080:
            return 8000.0
        return 4500.0

    def _estimate_converted_size_bytes(self, duration: float, target_bitrate_kbps: float) -> int:
        return int(duration * target_bitrate_kbps * 1000 / 8)

    def _collect_video_info(self, file_path: str) -> dict:
        ffprobe_path = os.path.join(FFMPEG_BIN, "ffprobe.exe")
        command = [
            ffprobe_path,
            "-v", "error",
            "-show_entries", "format=duration,size:stream=codec_name,width,height,avg_frame_rate",
            "-of", "json",
            file_path,
        ]

        try:
            creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            startup_info = None
            if hasattr(subprocess, "STARTUPINFO"):
                startup_info = subprocess.STARTUPINFO()
                startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startup_info.wShowWindow = subprocess.SW_HIDE

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                creationflags=creation_flags,
                startupinfo=startup_info,
            )
            data = json.loads(result.stdout)
            format_info = data.get("format", {})
            streams = data.get("streams", [])
            video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})

            width = int(video_stream.get("width", 0) or 0)
            height = int(video_stream.get("height", 0) or 0)
            fps_num, fps_den = (str(video_stream.get("avg_frame_rate", "0/0")).split("/", 1) + ["1"])[:2]
            fps = (int(fps_num) / int(fps_den)) if int(fps_den) else 0.0
            duration = float(format_info.get("duration", 0.0) or 0.0)
            codec = (video_stream.get("codec_name") or "Unknown").upper()
            file_size_bytes = int(format_info.get("size", os.path.getsize(file_path)) or os.path.getsize(file_path))
            frame_count = 0 if fps <= 0 else int(duration * fps)
        except Exception:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                raise ValueError("FFprobe and OpenCV could not open this file. Please choose a readable video file.")

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
            duration = frame_count / fps if fps > 0 else 0.0
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            codec = self._fourcc_to_string(fourcc)
            file_size_bytes = os.path.getsize(file_path)
            cap.release()

        file_size_mb = file_size_bytes / (1024 * 1024)
        bitrate_kbps = (file_size_bytes * 8) / (duration * 1000) if duration > 0 else 0.0
        recommended_bitrate_kbps = self._recommended_output_bitrate_kbps(width, height)
        estimated_converted_size_bytes = self._estimate_converted_size_bytes(duration, recommended_bitrate_kbps)

        return {
            "path": file_path,
            "file_size_bytes": file_size_bytes,
            "file_size_mb": file_size_mb,
            "width": width,
            "height": height,
            "fps": fps,
            "frame_count": frame_count,
            "duration": duration,
            "codec": codec,
            "bitrate_kbps": bitrate_kbps,
            "resolution": f"{width}x{height}",
            "estimated_quality_label": self._quality_label(width, height, fps, bitrate_kbps),
            "recommended_bitrate_kbps": recommended_bitrate_kbps,
            "estimated_converted_size_bytes": estimated_converted_size_bytes,
            "estimated_converted_size_display": self._format_file_size(estimated_converted_size_bytes),
        }

    def _fourcc_to_string(self, fourcc: int) -> str:
        chars = [chr((fourcc >> 8 * i) & 0xFF) for i in range(4)]
        return "".join(chars).strip() or "Unknown"

    def _quality_label(self, width: int, height: int, fps: float, bitrate_kbps: float) -> str:
        if width * height >= 3840 * 2160:
            return "Ultra HD / high bitrate"
        if width * height >= 1920 * 1080:
            return "Full HD"
        if width * height >= 1280 * 720:
            return "HD"
        return "SD / standard resolution"

    def _format_file_size(self, bytes_value: int) -> str:
        units = ["bytes", "KB", "MB", "GB", "TB"]
        size = float(bytes_value)
        unit_index = 0
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        if unit_index == 0:
            return f"{int(size)} bytes"
        return f"{size:.2f} {units[unit_index]}"

    def _render_folder_report(self, folder_path: str, info: dict, video_files: list[str]) -> None:
        lines = [
            "Folder Analysis Report",
            "=" * 80,
            f"Folder: {folder_path}",
            f"Video files found: {info['total_files']}",
            f"Total file size: {info['total_size_display']} ({sum(os.path.getsize(path) for path in video_files):,} bytes)",
            f"Total duration: {info['total_duration']:.2f} seconds",
            f"Average frame rate: {info['avg_fps']:.2f} fps",
            f"Dominant resolution: {info['dominant_resolution']}",
            f"Dominant codec: {info['dominant_codec']}",
            "",
            "Recommended combined-output settings for DaVinci Resolve:",
            f"- Output codec: {info['recommended_codec']}",
            f"- Output resolution: {info['recommended_resolution']}",
            f"- Frame rate: {info['recommended_fps']}",
            f"- Export preset: {info['recommended_preset']}",
            f"- Suggested bitrate: {info['recommended_bitrate']}",
            "",
            "DaVinci Resolve export guidance:",
            "- Use Delivery > H.264 or H.265 MP4 for a single final file.",
            "- Enable a quality-focused preset with the suggested bitrate above.",
            "- Keep the timeline at the highest resolution you truly need; avoid scaling to 4K unless the source is 4K.",
            "- If your destination is web/mobile, prefer H.264 with 1080p and 30 fps for the best size/quality balance.",
            "- If the target supports HEVC (H.265) and you want smaller files, use H.265 with the same resolution and a medium/slow preset.",
        ]

        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", "\n".join(lines))

        self.recommend_text.delete("1.0", "end")
        self.recommend_text.insert("1.0", "\n".join([
            "Best combined-output settings for the folder:",
            f"- Recommended codec: {info['recommended_codec']}",
            f"- Recommended resolution: {info['recommended_resolution']}",
            f"- Recommended frame rate: {info['recommended_fps']}",
            f"- Recommended preset: {info['recommended_preset']}",
            f"- Suggested bitrate: {info['recommended_bitrate']}",
            "",
            "DaVinci Resolve notes:",
            "1. Import the clips into a single timeline.",
            "2. Use Delivery > H.264/H.265 MP4 and choose a quality-focused preset.",
            "3. Match the output to your final audience (1080p for general use, 720p for mobile/web use).",
            "4. Keep audio at 192 kbps AAC for a good size/quality tradeoff.",
        ]))

        self.tools_text.delete("1.0", "end")
        self.tools_text.insert("1.0", "\n".join([
            "Recommended free tools for the combined output:",
            "1. FFmpeg: Use ffmpeg -i input.mp4 -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 192k output.mp4",
            "2. HandBrake: Export to H.264 or H.265 with a medium/slow preset and a quality-based RF/CRF value.",
            "3. DaVinci Resolve: Use Deliver > H.264/H.265 MP4 and choose a quality-focused preset for the final output.",
            "",
            "Quality and size guidance:",
            "- For the smallest files with modest quality loss, use H.265 and a medium/slow preset.",
            "- For maximum compatibility, choose H.264 and a medium preset.",
            "- Keep the final output at 1080p unless the source is truly 4K and you need the extra detail.",
        ]))

        self.last_report_text = "\n".join(lines)
        self.last_advice_text = self.recommend_text.get("1.0", "end")
        self.last_tools_text = self.tools_text.get("1.0", "end")

    def _render_report(self, file_path: str, info: dict) -> None:
        size_display = self._format_file_size(info["file_size_bytes"])
        duration_min = info["duration"] / 60
        duration_sec = info["duration"]

        lines = [
            "Video Analysis Report",
            "=" * 80,
            f"File: {file_path}",
            f"File size: {size_display}",
            f"Estimated converted size: {info['estimated_converted_size_display']} at ~{info['recommended_bitrate_kbps']:.0f} kbps",
            f"Duration: {duration_sec:.2f} seconds ({duration_min:.2f} minutes)",
            f"Resolution: {info['resolution']} ({info['estimated_quality_label']})",
            f"Frame rate: {info['fps']:.2f} fps",
            f"Frames: {info['frame_count']:,}",
            f"Codec / FourCC: {info['codec']}",
            f"Estimated bitrate: {info['bitrate_kbps']:.0f} kbps",
            "",
            "Quick interpretation:",
            self._interpretation(info),
            "",
            "Recommended reduction approach:",
        ]

        lines.append(self._recommendation_text(info))

        report_text = "\n".join(lines)
        advice_text = self._recommendation_text(info)
        tools_text = self._tool_recommendations(info)

        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", report_text)

        self.recommend_text.delete("1.0", "end")
        self.recommend_text.insert("1.0", advice_text)

        self.tools_text.delete("1.0", "end")
        self.tools_text.insert("1.0", tools_text)

        self.last_report_text = report_text
        self.last_advice_text = advice_text
        self.last_tools_text = tools_text

    def _interpretation(self, info: dict) -> str:
        notes = []
        if info["file_size_mb"] > 100:
            notes.append("The file is fairly large; lowering resolution or using a more efficient encoder can reduce size noticeably.")
        if info["fps"] > 30:
            notes.append("The source is high-frame-rate content; reducing to 24 or 30 fps can save space with little visual impact for most videos.")
        if info["width"] * info["height"] >= 1920 * 1080:
            notes.append("The video is high resolution; shrinking to 1080p or 720p can provide strong file-size savings without major quality loss.")
        if info["codec"] in ("avc1", "H264", "h264"):
            notes.append("The file is already H.264; changing to H.265/HEVC can be better for size reduction on compatible players.")
        return "\n".join(notes) if notes else "This video looks reasonably efficient for its current size and resolution."

    def _recommendation_text(self, info: dict) -> str:
        suggestions = []

        if info["width"] * info["height"] >= 3840 * 2160:
            suggestions.append("1. Downscale to 1920x1080 if the original 4K resolution is not essential for viewing.")
            suggestions.append("2. Use H.265/HEVC with CRF 24–28 for better compression at similar quality.")
        elif info["width"] * info["height"] >= 1920 * 1080:
            suggestions.append("1. Keep the resolution at 1080p, but consider 720p for mobile or web delivery if the original is not critical.")
            suggestions.append("2. Use H.264 CRF 18–23 or H.265 CRF 24–28 depending on compatibility needs.")
        else:
            suggestions.append("1. Keep the current resolution and use a moderate CRF level to preserve detail while reducing size.")
            suggestions.append("2. Reduce frame rate to 24–30 fps if the source is very high fps and the motion is smooth enough.")

        if info["fps"] > 30:
            suggestions.append("3. Lower the frame rate to 30 fps or 24 fps if the video is not highly motion-heavy.")

        if info["file_size_mb"] > 100:
            suggestions.append("4. Enable a slower preset (slow/medium) for better compression efficiency if you can accept longer encoding time.")

        suggestions.append("5. Prefer a two-pass or CRF-based encode instead of a fixed bitrate; CRF usually gives the best quality-to-size tradeoff.")
        return "\n".join(suggestions)

    def _tool_recommendations(self, info: dict) -> str:
        ffmpeg_cmd = self._build_ffmpeg_command(info)
        handbrake_presets = "- Preset: Fast 1080p30 (H.264) for general use\n- Preset: H.265 1080p30 (if your playback devices support HEVC)"

        return "\n".join([
            "Free tools to use:",
            "1. FFmpeg (best for command-line control)",
            "   Suggested command:",
            f"   {ffmpeg_cmd}",
            "",
            "2. HandBrake (best for a simple GUI)",
            f"   {handbrake_presets}",
            "",
            "3. VLC Media Player (good for quick conversion tests)",
            "   Use Media > Convert / Save, then choose H.264 + reasonable bitrate or a quality-based profile.",
            "",
            "Ideal configuration notes:",
            "- Use H.264 for maximum compatibility, H.265 for better size savings on modern devices.",
            "- Keep CRF in the 18–23 range for H.264, or 24–28 for H.265.",
            "- Use a medium or slow preset if the file is large and you can wait longer for encoding.",
            "- Scale down only when needed; avoid reducing resolution below 720p unless the destination is small screens.",
        ])

    def reset_view(self) -> None:
        self.path_var.set("")
        self.summary_text.delete("1.0", "end")
        self.recommend_text.delete("1.0", "end")
        self.tools_text.delete("1.0", "end")
        self.summary_text.insert("1.0", "Select a video file to generate the analysis report.\n")
        self.recommend_text.insert("1.0", "Suggestions will appear here after analysis.\n")
        self.tools_text.insert("1.0", "Recommended free tools and preset settings will appear here after analysis.\n")
        self.last_report_text = ""
        self.last_advice_text = ""
        self.last_tools_text = ""
        self._update_action_buttons("")
        self.status_var.set("Reset complete. Choose a new video file to begin.")

    def save_report(self) -> None:
        if not getattr(self, "last_report_text", ""):
            messagebox.showinfo("Nothing to save", "Please analyze a video file before saving the report.")
            return

        file_path = self.path_var.get().strip()
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Missing file", "Please choose a valid video file before saving the report.")
            return

        folder = os.path.dirname(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_path = os.path.join(folder, f"{base_name}_analysis_report.txt")

        try:
            with open(output_path, "w", encoding="utf-8") as handle:
                handle.write("VIDEO ANALYSIS REPORT\n")
                handle.write("=" * 80 + "\n\n")
                handle.write(self.last_report_text + "\n\n")
                handle.write("OPTIMIZATION ADVICE\n")
                handle.write("=" * 80 + "\n\n")
                handle.write(self.last_advice_text + "\n\n")
                handle.write("FREE TOOLS AND SETTINGS\n")
                handle.write("=" * 80 + "\n\n")
                handle.write(self.last_tools_text + "\n")

            self.status_var.set(f"Report saved next to the video file: {output_path}")
            messagebox.showinfo("Report saved", f"The analysis report was saved here:\n\n{output_path}")
        except Exception as exc:
            messagebox.showerror("Save failed", f"Unable to save the report.\n\n{exc}")

    def _build_ffmpeg_command(self, info: dict) -> str:
        ffmpeg_path = os.path.join(FFMPEG_BIN, "ffmpeg.exe")
        width = info["width"]
        height = info["height"]
        fps = info["fps"]

        scale_filter = ""
        if width >= 3840 or height >= 2160:
            scale_filter = " -vf \"scale=1920:1080\""
        elif width > 1920 or height > 1080:
            scale_filter = " -vf \"scale=1920:1080\""

        fps_filter = ""
        if fps > 30:
            fps_filter = " -r 30"

        codec = "libx265" if info["codec"] not in ("H264", "h264", "avc1") else "libx264"
        crf = "28" if codec == "libx265" else "23"

        return f'"{ffmpeg_path}" -i "input.mp4"{scale_filter}{fps_filter} -c:v {codec} -preset medium -crf {crf} -c:a aac -b:a 128k "optimized.mp4"'


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoOptimizerAdvisorApp(root)
    root.mainloop()
