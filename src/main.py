#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path
from language_detector.audio_detector import AudioLanguageDetector
from language_detector.mkv_processor import MKVProcessor


def parse_args():
    parser = argparse.ArgumentParser(
        description="Process MKV files to detect spoken language using subtitle timing"
    )
    parser.add_argument("mkv_file", type=str, help="Path to MKV file to process")
    parser.add_argument(
        "--save-srt", action="store_true", help="Save the extracted SRT file"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        help="Path to previously downloaded language detection model",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output JSON file for results (defaults to {input_name}_results.json)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main():
    args = parse_args()

    # Validate input file
    mkv_path = Path(args.mkv_file)
    if not mkv_path.exists():
        print(f"Error: Input file does not exist: {mkv_path}")
        sys.exit(1)

    # Set up output path if not specified
    if not args.output:
        args.output = mkv_path.with_suffix(".results.json")

    try:
        # Initialize detector and processor
        detector = AudioLanguageDetector(model_path=args.model_path)
        processor = MKVProcessor(str(mkv_path))

        # Process the file
        print(f"\nProcessing: {mkv_path}")
        results = processor.process_with_detector(
            detector, save_srt=args.save_srt, debug=args.debug
        )

        # Print summary
        print("\nProcessing Results:")
        for result in results:
            print(f"\nSegment {result['segment']}:")
            print(f"Time: {result['start_time']:.2f}s - {result['end_time']:.2f}s")
            print(f"Detected Language: {result['detected_language']}")
            print(f"Confidence: {result['confidence']:.2f}")

        # Save results
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {args.output}")

    except Exception as e:
        print(f"Error processing file: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
