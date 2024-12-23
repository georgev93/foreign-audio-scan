import torch
import torchaudio
import subprocess
import os
from speechbrain.pretrained import EncoderClassifier
from pathlib import Path
import tempfile


class AudioLanguageDetector:
    def __init__(self):
        """Initialize the language detector with VoxLingua107 model"""
        self.classifier = EncoderClassifier.from_hparams(
            source="speechbrain/lang-id-voxlingua107-ecapa", savedir="tmp/voxlingua107"
        )
        self.language_mapping = {"en": "English", "ru": "Russian"}

    def extract_audio(self, mkv_file, output_dir=None):
        """
        Extract audio from MKV file to WAV format
        Returns path to extracted audio file
        """
        if output_dir is None:
            output_dir = tempfile.gettempdir()

        output_path = os.path.join(output_dir, f"{Path(mkv_file).stem}_audio.wav")

        # FFmpeg command to extract audio and convert to WAV
        command = [
            "ffmpeg",
            "-i",
            mkv_file,  # Input file
            "-vn",  # Disable video
            "-acodec",
            "pcm_s16le",  # Convert to PCM WAV
            "-ar",
            "16000",  # Set sample rate to 16kHz
            "-ac",
            "1",  # Convert to mono
            "-y",  # Overwrite output file if exists
            output_path,
        ]

        try:
            subprocess.run(command, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to extract audio: {e.stderr.decode()}")

    def detect_language(self, audio_file, segment_duration=30):
        """
        Detect language from audio file using VoxLingua107.
        Args:
            audio_file: Path to audio file
            segment_duration: Duration in seconds for each segment to analyze
        Returns dictionary with detected language and confidence score
        """
        signal, fs = torchaudio.load(audio_file)

        # Convert segment duration to samples
        segment_len = segment_duration * fs
        num_segments = signal.shape[1] // segment_len

        results = []
        # Process each segment
        for i in range(num_segments):
            start = i * segment_len
            end = start + segment_len
            segment = signal[:, start:end]

            # Make prediction
            prediction = self.classifier.classify_batch(segment)

            # Get the predicted language and score
            language = prediction[0].argmax().item()
            score = prediction[1].max().item()

            predicted_lang = self.classifier.hparams.label_encoder.decode_ndim(language)
            results.append(
                {
                    "language": self.language_mapping.get(
                        predicted_lang, predicted_lang
                    ),
                    "confidence": score,
                    "segment": i,
                }
            )

        # Aggregate results
        language_counts = {}
        for result in results:
            lang = result["language"]
            language_counts[lang] = language_counts.get(lang, 0) + 1

        # Get the most common language
        dominant_language = max(language_counts.items(), key=lambda x: x[1])[0]

        # Calculate average confidence for dominant language
        confidence_scores = [
            r["confidence"] for r in results if r["language"] == dominant_language
        ]
        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        )

        return {
            "language": dominant_language,
            "confidence": avg_confidence,
            "segments": results,
        }

    def process_mkv(self, mkv_file, cleanup=True):
        """
        Process MKV file and detect language
        Args:
            mkv_file: Path to MKV file
            cleanup: Whether to delete temporary WAV file after processing
        """
        try:
            # Extract audio from MKV
            wav_file = self.extract_audio(mkv_file)

            # Detect language
            result = self.detect_language(wav_file)

            # Cleanup temporary file if requested
            if cleanup:
                os.remove(wav_file)

            return result

        except Exception as e:
            if cleanup and "wav_file" in locals():
                try:
                    os.remove(wav_file)
                except:
                    pass
            raise e


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Detect language in MKV file")
    parser.add_argument("mkv_file", type=str, help="Path to MKV file")
    parser.add_argument(
        "--keep-wav",
        action="store_true",
        help="Keep extracted WAV file after processing",
    )
    args = parser.parse_args()

    try:
        detector = AudioLanguageDetector()
        result = detector.process_mkv(args.mkv_file, cleanup=not args.keep_wav)

        print(f"\nDominant language: {result['language']}")
        print(f"Average confidence: {result['confidence']:.2f}")

        print("\nSegment analysis:")
        for segment in result["segments"]:
            print(
                f"Segment {segment['segment']}: {segment['language']} "
                f"(confidence: {segment['confidence']:.2f})"
            )

    except Exception as e:
        print(f"Error processing MKV file: {str(e)}")


if __name__ == "__main__":
    main()
