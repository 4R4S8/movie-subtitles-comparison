import pysrt
import csv
import sys
import os
from pathlib import Path
import chardet

def detect_encoding(file_path):
    """More robust encoding detection with fallbacks"""
    try:
        with open(file_path, "rb") as f:
            raw_data = f.read(10000)  # read more data for better detection
            
        # Try chardet first
        result = chardet.detect(raw_data)
        if result['confidence'] > 0.7:
            detected_encoding = result['encoding'].lower()
            # Map common encodings to proper names
            encoding_map = {
                'windows-1252': 'cp1252',
                'iso-8859-1': 'latin-1',
                'iso-8859-9': 'latin-5',
            }
            return encoding_map.get(detected_encoding, detected_encoding)
        
        # Fallback: check for UTF-8 BOM
        if raw_data.startswith(b'\xef\xbb\xbf'):
            return 'utf-8-sig'
            
        # Fallback: try common encodings
        for encoding in ['utf-8', 'cp1252', 'latin-1', 'iso-8859-1']:
            try:
                raw_data.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue
                
    except Exception as e:
        print(f"   ⚠️  Encoding detection failed: {e}")
    
    return 'utf-8'  # ultimate fallback

def load_subs(filename):
    """Load SRT file with robust encoding handling"""
    max_attempts = 3
    encodings_to_try = []
    
    # First, try detected encoding
    detected_encoding = detect_encoding(filename)
    encodings_to_try.append(detected_encoding)
    
    # Add common fallbacks
    encodings_to_try.extend(['utf-8-sig', 'utf-8', 'cp1252', 'latin-1', 'iso-8859-1'])
    
    for encoding in encodings_to_try[:max_attempts]:
        try:
            subs = pysrt.open(filename, encoding=encoding)
            result = []
            for sub in subs:
                start = sub.start.hours * 3600 + sub.start.minutes * 60 + sub.start.seconds + sub.start.milliseconds / 1000
                end = sub.end.hours * 3600 + sub.end.minutes * 60 + sub.end.seconds + sub.end.milliseconds / 1000
                text = sub.text.replace("\n", " ").strip()
                result.append((start, end, text))
            print(f"   ✅ Successfully loaded with encoding: {encoding}")
            return result
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"   ⚠️  Failed with encoding {encoding}: {e}")
            continue
    
    # If all attempts fail, try with error handling
    try:
        print(f"   ⚠️  Trying with error handling...")
        subs = pysrt.open(filename, encoding='utf-8', error_handling='ignore')
        result = []
        for sub in subs:
            start = sub.start.hours * 3600 + sub.start.minutes * 60 + sub.start.seconds + sub.start.milliseconds / 1000
            end = sub.end.hours * 3600 + sub.end.minutes * 60 + sub.end.seconds + sub.end.milliseconds / 1000
            text = sub.text.replace("\n", " ").strip()
            result.append((start, end, text))
        return result
    except Exception as e:
        print(f"   ❌ Failed to load {filename}: {e}")
        return []

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

def process_movie_folder(movie_folder, output_file=None):
    """Process a single movie folder and generate comparison CSV"""
    movie_folder = Path(movie_folder)
    
    # Set default output filename if not provided
    if output_file is None:
        output_file = movie_folder / f"{movie_folder.name}_comparison.csv"
    else:
        output_file = Path(output_file)
    
    # English subtitle
    english_file = movie_folder / "english_subtitle.srt"
    if not english_file.exists():
        print(f"❌ Could not find english_subtitle.srt in {movie_folder}")
        return False

    # Persian subtitles
    persian_folder = movie_folder / "persian"
    if not persian_folder.exists():
        print(f"❌ No persian folder found in {movie_folder}")
        return False
        
    persian_files = sorted(persian_folder.glob("*.srt"))
    if not persian_files:
        print(f"❌ No Persian subtitle files found in {persian_folder}")
        return False

    print(f"📁 Processing: {movie_folder.name}")
    print(f"   ✅ Found {len(persian_files)} Persian subtitle files.")

    # Load subtitles with error handling
    print(f"   📖 Loading English subtitle...")
    english_subs = load_subs(english_file)
    if not english_subs:
        print(f"   ❌ Failed to load English subtitle")
        return False

    # Load Persian subtitles
    persian_subs_all = []
    successful_persian_files = []
    
    for persian_file in persian_files:
        print(f"   📖 Loading {persian_file.name}...")
        persian_subs = load_subs(persian_file)
        if persian_subs:
            persian_subs_all.append(persian_subs)
            successful_persian_files.append(persian_file)
        else:
            print(f"   ❌ Skipping {persian_file.name} due to loading error")

    if not persian_subs_all:
        print(f"   ❌ No Persian subtitles could be loaded successfully")
        return False

    # Write CSV
    try:
        with open(output_file, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            header = ["Start Time", "End Time", "English"] + [f.name for f in successful_persian_files]
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

        print(f"   💾 Comparison saved to {output_file}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error writing CSV: {e}")
        return False

def main():
    # Default values
    data_folder = "Data"
    default_csv_name = "subtitle_comparison.csv"
    
    # Parse command line arguments
    if len(sys.argv) == 1:
        # No arguments: process all folders in Data directory
        target_folders = [f for f in Path(data_folder).iterdir() if f.is_dir()]
        output_files = [None] * len(target_folders)
        
    elif len(sys.argv) == 2:
        # One argument: could be a folder or CSV name
        arg = sys.argv[1]
        if Path(arg).is_dir():
            target_folders = [Path(arg)]
            output_files = [None]
        else:
            target_folders = [f for f in Path(data_folder).iterdir() if f.is_dir()]
            output_files = [Path(data_folder) / arg] * len(target_folders)
            
    elif len(sys.argv) == 3:
        # Two arguments: specific folder and specific CSV
        target_folders = [Path(sys.argv[1])]
        output_files = [sys.argv[2]]
        
    else:
        print("Usage: python compare_folder.py [movie_folder] [output.csv]")
        print("  No arguments: process all folders in Data/ with default naming")
        print("  One argument: process specific folder or use custom CSV name for Data/")
        print("  Two arguments: process specific folder with specific CSV file")
        sys.exit(1)

    # Process all target folders
    success_count = 0
    total_count = len(target_folders)
    
    for i, (movie_folder, output_file) in enumerate(zip(target_folders, output_files), 1):
        if not movie_folder.is_dir():
            print(f"❌ Skipping non-directory: {movie_folder}")
            continue
            
        print(f"\n[{i}/{total_count}] ", end="")
        if process_movie_folder(movie_folder, output_file):
            success_count += 1
    
    print(f"\n🎉 Completed! Successfully processed {success_count}/{total_count} folders.")

if __name__ == "__main__":
    main()