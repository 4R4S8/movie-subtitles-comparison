import pysrt
import json
import sys
from pathlib import Path
import chardet

def debug_print(message):
    """Simple debug printing"""
    print(f"   🔍 {message}")

def detect_encoding_correctly(file_path):
    """Better encoding detection with Persian language focus"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(50000)  # Read more data for better detection
        
        # First, check for UTF-8 BOM
        if raw_data.startswith(b'\xef\xbb\xbf'):
            return 'utf-8-sig'
        
        # Use chardet for initial detection
        result = chardet.detect(raw_data)
        
        # For Persian/Unicode text, prefer UTF-8 variants
        if result['encoding'] and result['confidence'] > 0.7:
            detected = result['encoding'].lower()
            
            # Common Persian encodings mapping
            encoding_map = {
                'windows-1256': 'cp1256',  # Arabic/Persian Windows encoding
                'iso-8859-6': 'iso-8859-6',  # Arabic encoding
                'utf-8': 'utf-8',
                'ascii': 'utf-8',  # Force UTF-8 for ASCII detection
            }
            
            return encoding_map.get(detected, 'utf-8')
        
        # If detection fails, try to identify Persian text patterns
        # Persian text often contains specific Unicode ranges
        try:
            # Try UTF-8 first (most common for modern subtitles)
            raw_data.decode('utf-8')
            return 'utf-8'
        except:
            # Try Windows-1256 (common for Persian/Arabic)
            try:
                raw_data.decode('cp1256')
                return 'cp1256'
            except:
                # Final fallback
                return 'utf-8'
                
    except Exception as e:
        debug_print(f"Encoding detection error: {e}")
        return 'utf-8'

def is_valid_persian_text(text):
    """Check if text contains valid Persian characters or is empty"""
    if not text.strip():
        return True  # Empty text is valid
    
    # Persian/Arabic Unicode ranges
    persian_ranges = [
        (0x0600, 0x06FF),   # Arabic block
        (0x0750, 0x077F),   # Arabic Supplement
        (0x08A0, 0x08FF),   # Arabic Extended-A
        (0xFB50, 0xFDFF),   # Arabic Presentation Forms-A
        (0xFE70, 0xFEFF),   # Arabic Presentation Forms-B
    ]
    
    # Also allow basic Latin for numbers and punctuation
    latin_ranges = [
        (0x0020, 0x007F),   # Basic Latin
    ]
    
    for char in text:
        char_code = ord(char)
        valid = False
        
        # Check if character is in any valid range
        for range_start, range_end in persian_ranges + latin_ranges:
            if range_start <= char_code <= range_end:
                valid = True
                break
        
        if not valid:
            return False
    
    return True

def load_subtitle_file_correctly(filename):
    """Load subtitle file with proper Persian encoding handling"""
    try:
        # Detect encoding specifically for Persian text
        encoding = detect_encoding_correctly(filename)
        debug_print(f"Using encoding: {encoding} for {filename.name}")
        
        # Load with the detected encoding
        subs = pysrt.open(filename, encoding=encoding)
        results = []
        
        for sub in subs:
            # Format time
            start_str = f"{sub.start.hours:02}:{sub.start.minutes:02}:{sub.start.seconds:02}"
            end_str = f"{sub.end.hours:02}:{sub.end.minutes:02}:{sub.end.seconds:02}"
            
            if sub.start.milliseconds > 0:
                start_str += f".{sub.start.milliseconds:03}"
            if sub.end.milliseconds > 0:
                end_str += f".{sub.end.milliseconds:03}"
            
            text = sub.text.replace("\n", " ").strip()
            
            # Fix encoding issues if text is garbled
            if text and not is_valid_persian_text(text):
                debug_print(f"Found garbled text, trying to fix encoding: {text[:50]}...")
                # Try to re-encode with different encodings
                text = fix_garbled_text(text, encoding)
            
            results.append((start_str, end_str, text))
        
        debug_print(f"Successfully loaded {len(results)} lines")
        return results
        
    except Exception as e:
        debug_print(f"Failed to load {filename.name}: {str(e)}")
        # Try one more time with UTF-8 and error ignoring
        try:
            subs = pysrt.open(filename, encoding='utf-8', error_handling='ignore')
            results = []
            for sub in subs:
                start_str = f"{sub.start.hours:02}:{sub.start.minutes:02}:{sub.start.seconds:02}"
                end_str = f"{sub.end.hours:02}:{sub.end.minutes:02}:{sub.end.seconds:02}"
                if sub.start.milliseconds > 0:
                    start_str += f".{sub.start.milliseconds:03}"
                if sub.end.milliseconds > 0:
                    end_str += f".{sub.end.milliseconds:03}"
                text = sub.text.replace("\n", " ").strip()
                results.append((start_str, end_str, text))
            debug_print(f"Loaded with UTF-8 fallback: {len(results)} lines")
            return results
        except:
            return []

def fix_garbled_text(text, original_encoding):
    """Try to fix Mojibake (garbled text)"""
    common_fixes = [
        # Common encoding issues and their fixes
        ('utf-8', 'cp1256'),  # UTF-8 misinterpreted as Windows-1256
        ('cp1256', 'utf-8'),  # Windows-1256 misinterpreted as UTF-8
        ('iso-8859-1', 'utf-8'),
        ('windows-1252', 'utf-8'),
    ]
    
    for wrong_enc, correct_enc in common_fixes:
        try:
            # Try to decode with wrong encoding and then encode with correct one
            fixed = text.encode(wrong_enc).decode(correct_enc)
            if is_valid_persian_text(fixed):
                debug_print(f"Fixed text: {text[:30]} -> {fixed[:30]}")
                return fixed
        except:
            continue
    
    # If all fixes fail, return empty string to avoid garbage
    debug_print(f"Could not fix garbled text: {text[:50]}")
    return ""

def time_to_seconds_simple(time_str):
    """Convert time string to seconds"""
    try:
        if '.' in time_str:
            time_part, ms_part = time_str.split('.')
            ms = float(f"0.{ms_part}")
        else:
            time_part = time_str
            ms = 0
        
        parts = time_part.split(':')
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds + ms
        return 0
    except:
        return 0

def find_best_match_simple(eng_start, eng_end, persian_subs):
    """Find matching translation"""
    if not persian_subs:
        return ""
    
    eng_start_sec = time_to_seconds_simple(eng_start)
    eng_end_sec = time_to_seconds_simple(eng_end)
    
    best_match = ""
    best_score = -1
    
    for ps_start, ps_end, ps_text in persian_subs:
        if not ps_text.strip():
            continue
            
        ps_start_sec = time_to_seconds_simple(ps_start)
        ps_end_sec = time_to_seconds_simple(ps_end)
        
        overlap_start = max(eng_start_sec, ps_start_sec)
        overlap_end = min(eng_end_sec, ps_end_sec)
        overlap = max(0, overlap_end - overlap_start)
        
        start_diff = abs(eng_start_sec - ps_start_sec)
        score = overlap * 10 - start_diff
        
        if score > best_score:
            best_score = score
            best_match = ps_text
    
    return best_match

def find_persian_subtitles(movie_folder):
    """Find Persian subtitle files"""
    folders_to_check = ['opensubtitle', 'subkade']
    found_files = {}
    
    for folder_name in folders_to_check:
        folder_path = movie_folder / folder_name
        if folder_path.exists():
            srt_files = [f for f in folder_path.glob("*.srt") 
                        if 'english' not in f.name.lower() and 'en.' not in f.name.lower()]
            if srt_files:
                found_files[folder_name] = srt_files
                debug_print(f"Found {len(srt_files)} files in {folder_name}")
    
    return found_files

def process_movie(movie_path):
    """Main processing function"""
    debug_print(f"Starting processing for {movie_path.name}")
    
    # Load English subtitle
    english_file = movie_path / "english_subtitle.srt"
    if not english_file.exists():
        english_files = list(movie_path.glob("*english*.srt")) + list(movie_path.glob("*en*.srt"))
        if english_files:
            english_file = english_files[0]
            debug_print(f"Using alternative English file: {english_file.name}")
        else:
            debug_print("No English subtitle file found")
            return None
    
    english_subs = load_subtitle_file_correctly(english_file)
    if not english_subs:
        return None
    
    # Find and load Persian subtitles
    persian_files = find_persian_subtitles(movie_path)
    if not persian_files:
        return None
    
    all_persian_subs = {}
    file_mapping = {}
    
    for folder_name, files in persian_files.items():
        all_persian_subs[folder_name] = {}
        file_mapping[folder_name] = {}
        
        for i, file_path in enumerate(files, 1):
            sub_name = f"subtitle_{i:02d}"
            file_mapping[folder_name][sub_name] = file_path.name
            
            subs = load_subtitle_file_correctly(file_path)
            if subs:
                all_persian_subs[folder_name][sub_name] = subs
            else:
                all_persian_subs[folder_name][sub_name] = []
    
    # Create JSON
    result = {
        "movie": movie_path.name,
        "file_mapping": file_mapping,
        "subtitles": []
    }
    
    for eng_start, eng_end, eng_text in english_subs:
        entry = {
            "time": f"{eng_start},{eng_end}",
            "english": eng_text,
            "translations": {}
        }
        
        for folder_name, subs_dict in all_persian_subs.items():
            entry["translations"][folder_name] = {}
            for sub_name, persian_subs in subs_dict.items():
                translation = find_best_match_simple(eng_start, eng_end, persian_subs)
                entry["translations"][folder_name][sub_name] = translation
        
        result["subtitles"].append(entry)
    
    return result

def main():
    print("🎬 Starting Persian Subtitle Matcher")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        movie_folders = [Path(sys.argv[1])]
    else:
        data_folder = Path("Data")
        movie_folders = [f for f in data_folder.iterdir() if f.is_dir()]
    
    successful = 0
    for movie_folder in movie_folders:
        print(f"\n📁 Processing: {movie_folder.name}")
        print("-" * 30)
        
        result = process_movie(movie_folder)
        if result:
            output_file = movie_folder / f"{movie_folder.name}_comparison.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"✅ SUCCESS: Saved to {output_file}")
            successful += 1
        else:
            print(f"❌ FAILED: Could not process {movie_folder.name}")
    
    print(f"\n🎉 Finished! {successful}/{len(movie_folders)} movies processed successfully")

if __name__ == "__main__":
    main()