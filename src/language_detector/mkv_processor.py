from pymkv import MKVFile
import pysubs2
import subprocess
import os
from pathlib import Path
from typing import List, Optional
from .utils import SubtitleSegment, SubtitleTrack


class MKVProcessor:
    def __init__(self, mkv_path: str):
        self.mkv_path = mkv_path
        self.mkv = MKVFile(mkv_path)

    def list_subtitle_tracks(self) -> List[SubtitleTrack]:
        """List all subtitle tracks in the MKV file"""
        subtitle_tracks = []
        for track in self.mkv.tracks:
            if track.track_type == "subtitles":
                subtitle_tracks.append(
                    SubtitleTrack(
                        id=track.track_id,
                        codec=track.codec,
                        language=track.language,
                        name=track.name,
                    )
                )
        return subtitle_tracks

    def extract_subtitle_track(
        self, track_id: int, output_dir: Optional[str] = None
    ) -> str:
        """Extract a subtitle track to a file"""
        if output_dir is None:
            output_dir = os.getcwd()

        # Create safe filename from original MKV name
        base_name = Path(self.mkv_path).stem
        output_path = os.path.join(output_dir, f"{base_name}_track_{track_id}.sup")

        cmd = ["mkvextract", self.mkv_path, "tracks", f"{track_id}:{output_path}"]

        try:
            print(f"Extracting subtitle track {track_id} to {output_path}")
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"Error extracting subtitles: {e.stdout}\n{e.stderr}")
            raise

    def convert_pgs_to_srt(
        self, sup_path: str, output_dir: Optional[str] = None
    ) -> str:
        """Convert PGS/SUP subtitle to SRT format using OCR"""
        if output_dir is None:
            output_dir = os.getcwd()

        output_path = os.path.join(output_dir, f"{Path(sup_path).stem}.srt")

        cmd = [
            "subtitle-edit-cli",
            "/convert",
            sup_path,
            "/target:srt",
            f"/outputfolder:{output_dir}",
        ]

        try:
            print(f"Converting {sup_path} to SRT format")
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"Error converting subtitles: {e.stdout}\n{e.stderr}")
            raise

    def parse_srt_segments(self, srt_path: str) -> List[SubtitleSegment]:
        """Parse SRT file and return list of subtitle segments with timing information"""
        subs = pysubs2.load(srt_path)
        segments = []

        for event in subs:
            start_time = event.start / 1000.0  # Convert ms to seconds
            end_time = event.end / 1000.0
            duration = end_time - start_time

            segments.append(
                SubtitleSegment(
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    text=event.text,
                )
            )

        return segments

    def extract_audio_segment(
        self, start_time: float, end_time: float, output_dir: Optional[str] = None
    ) -> str:
        """Extract audio segment from MKV file based on timestamp range"""
        if output_dir is None:
            output_dir = os.getcwd()

        output_path = os.path.join(
            output_dir, f"segment_{start_time:.3f}_{end_time:.3f}.wav"
        )

        cmd = [
            "ffmpeg",
            "-i",
            self.mkv_path,
            "-ss",
            str(start_time),
            "-t",
            str(end_time - start_time),
            "-vn",  # No video
            "-acodec",
            "pcm_s16le",  # PCM 16-bit output
            "-ar",
            "16000",  # 16kHz sampling rate
            "-ac",
            "1",  # Mono
            "-y",  # Overwrite output file
            output_path,
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"Error extracting audio segment: {e.stdout}\n{e.stderr}")
            raise
