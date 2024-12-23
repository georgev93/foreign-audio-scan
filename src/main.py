import os
import subprocess
import argparse
from pydub import AudioSegment
from langdetect import detect
from pysubparser import parser


def extract_audio(mkv_file):
    audio_file = mkv_file.replace(".mkv", ".mp3")
    command = f"ffmpeg -i {mkv_file} -q:a 0 -map a {audio_file} -y"
    subprocess.call(command, shell=True)
    return audio_file


def split_audio(audio_file):
    audio = AudioSegment.from_file(audio_file)
    chunks = [audio[i : i + 10000] for i in range(0, len(audio), 10000)]
    chunk_files = []
    for i, chunk in enumerate(chunks):
        chunk_file = f"chunk_{i}.mp3"
        chunk.export(chunk_file, format="mp3")
        chunk_files.append(chunk_file)
    return chunk_files


def transcribe_audio(chunk_file):
    # Placeholder function for transcribing audio to text.
    # Replace this with actual transcription logic if available.
    # For offline use, you may need a local speech recognition model.
    return "transcribed text"


def detect_language(chunk_files):
    non_english_segments = []
    for i, chunk_file in enumerate(chunk_files):
        text = transcribe_audio(chunk_file)
        language = detect(text)
        if language != "en":
            start_time = i * 10
            end_time = start_time + 10
            non_english_segments.append((start_time, end_time))
    return non_english_segments


def process_subtitles(mkv_file, non_english_segments):
    subtitle_file = mkv_file.replace(".mkv", ".srt")
    modified_subtitle_file = mkv_file.replace(".mkv", "_modified.srt")
    command = f"ffmpeg -i {mkv_file} -map 0:s:0 {subtitle_file} -y"
    subprocess.call(command, shell=True)

    subtitles = parser.parse(subtitle_file)
    with open(modified_subtitle_file, "w") as f:
        for subtitle in subtitles:
            if any(
                (start <= subtitle.start <= end) or (start <= subtitle.end <= end)
                for start, end in non_english_segments
            ):
                f.write(str(subtitle))

    return modified_subtitle_file


def re_add_subtitles(mkv_file, subtitle_file):
    new_mkv_file = mkv_file.replace(".mkv", "_new.mkv")
    command = f"ffmpeg -i {mkv_file} -i {
        subtitle_file} -map 0 -map 1 -c copy -disposition:s:1 forced {
        new_mkv_file} -y"
    subprocess.call(command, shell=True)


def main(mkv_file):
    print(mkv_file)
    audio_file = extract_audio(mkv_file)
    chunk_files = split_audio(audio_file)
    non_english_segments = detect_language(chunk_files)
    print("Non-English segments:", non_english_segments)
    # modified_subtitle_file = process_subtitles(mkv_file, non_english_segments)
    # re_add_subtitles(mkv_file, modified_subtitle_file)


if __name__ == "__main__":
    # main('samples/russian.mkv')
    myParser = argparse.ArgumentParser(
        description="Process an MKV file for non-English audio segments and subtitles."
    )
    myParser.add_argument("mkv_file", type=str, help="Path to the MKV file")
    args = myParser.parse_args()
    main(args.mkv_file)
