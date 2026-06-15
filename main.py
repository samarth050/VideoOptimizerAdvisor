import json
import os
import subprocess
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
            text="Pick a video file to inspect its characteristics, estimate size, and receive quality-preserving optimization suggestions.",
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

        browse_btn = ttk.Button(pick_frame, text="Browse…", command=self.choose_file)
        browse_btn.pack(side="left", padx=(8, 0))

        button_row = ttk.Frame(main)
        button_row.pack(anchor="w", pady=(0, 10))

        analyze_btn = ttk.Button(button_row, text="Analyze Video", command=self.analyze_video)
        analyze_btn.pack(side="left")

        save_btn = ttk.Button(button_row, text="Save Report", command=self.save_report)
        save_btn.pack(side="left", padx=(8, 0))

        reset_btn = ttk.Button(button_row, text="Reset", command=self.reset_view)
        reset_btn.pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value="Ready. Select a video file to begin.")
        status = ttk.Label(main, textvariable=self.status_var, foreground="#1f5fbf", font=("Segoe UI", 10))
        status.pack(anchor="w", pady=(0, 8))

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
            self.status_var.set("File selected. Click Analyze Video to inspect it.")

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
            result = subprocess.run(command, capture_output=True, text=True, check=True)
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

    def _render_report(self, file_path: str, info: dict) -> None:
        size_display = self._format_file_size(info["file_size_bytes"])
        duration_min = info["duration"] / 60
        duration_sec = info["duration"]

        lines = [
            "Video Analysis Report",
            "=" * 80,
            f"File: {file_path}",
            f"File size: {size_display}",
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
