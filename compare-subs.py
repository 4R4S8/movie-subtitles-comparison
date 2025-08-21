import pysrt
import csv
import sys
import os
from pathlib import Path
import chardet

def detect_encoding(file_path):
    with open(file_path, "rb") as f:
        raw_data = f.read(5000)  # read first few KB
    result = chardet.detect(raw_data)
    return result["encoding"] or "utf-8"

def load_subs(filename):
    """Load SRT file with auto-detected encoding"""
    encoding = detect_encoding(filename)
    subs = pysrt.open(filename, encoding=encoding)
    result = []
    for sub in subs:
        start = sub.start.hours * 3600 + sub.start.minutes * 60 + sub.start.seconds + sub.start.milliseconds / 1000
        end = sub.end.hours * 3600 + sub.end.minutes * 60 + sub.end.seconds + sub.end.milliseconds / 1000
        text = sub.text.replace("\n", " ").strip()
        result.append((start, end, text))
    return result

def find_best_match(en_start, en_end, persian_list):
    """Find Persian subtitle with the most overlap in time"""
    best_match = ""
    best_overlap = 0
    for (ps_start, ps_end, ps_text) in persian_list:
        overlap_start = max(en_start, ps_start)
        overlap_end = min(en_end, ps_end)
        overlap = max(0, overlap_end - overlap_start)
        if overlap > best_overlap:
            best_overlap = overlap
            best_match = ps_text
    return best_match

def main():
    if len(sys.argv) != 3:
        print("Usage: python compare_folder.py <movie_folder> <output.csv>")
        sys.exit(1)

    movie_folder = Path(sys.argv[1])
    output_file = sys.argv[2]

    # English subtitle
    english_file = movie_folder / "english_subtitle.srt"
    if not english_file.exists():
        print(f"❌ Could not find english_subtitle.srt in {movie_folder}")
        sys.exit(1)

    # Persian subtitles
    persian_folder = movie_folder / "persian"
    persian_files = sorted(persian_folder.glob("*.srt"))
    if not persian_files:
        print(f"❌ No Persian subtitles found in {persian_folder}")
        sys.exit(1)

    print(f"✅ Found {len(persian_files)} Persian subtitle files.")

    # Load subtitles
    english_subs = load_subs(english_file)
    persian_subs_all = [load_subs(f) for f in persian_files]

    # Write CSV
    with open(output_file, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["Start Time", "End Time", "English"] + [f.name for f in persian_files]
        writer.writerow(header)

        for (en_start, en_end, en_text) in english_subs:
            row = [
                f"{int(en_start//60):02}:{int(en_start%60):02}",
                f"{int(en_end//60):02}:{int(en_end%60):02}",
                en_text
            ]
            for persian_list in persian_subs_all:
                row.append(find_best_match(en_start, en_end, persian_list))
            writer.writerow(row)

    print(f"✅ Comparison saved to {output_file}")

if __name__ == "__main__":
    main()
