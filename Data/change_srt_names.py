import os
import shutil
from pathlib import Path

def rename_english_subtitles(root_dir):
    """
    Rename all .srt files in level 1 folders (movie directories) 
    to 'english_subtitle.srt', excluding files in persian/ and archive/ subfolders
    """
    root_path = Path(root_dir)
    
    # Get all movie directories (level 1 folders)
    for movie_dir in root_path.iterdir():
        if movie_dir.is_dir():
            print(f"Checking directory: {movie_dir.name}")
            
            # Look for .srt files in this movie directory
            for file_path in movie_dir.iterdir():
                if (file_path.is_file() and 
                    file_path.suffix.lower() == '.srt' and 
                    not any(part in ['persian', 'archive'] for part in file_path.parts)):
                    
                    # Create new path for the renamed file
                    new_path = file_path.parent / "english_subtitle.srt"
                    
                    try:
                        # Rename the file
                        shutil.move(str(file_path), str(new_path))
                        print(f"  ✓ Renamed: {file_path.name} -> english_subtitle.srt")
                    except Exception as e:
                        print(f"  ✗ Error renaming {file_path.name}: {e}")

def preview_changes(root_dir):
    """
    Preview what files would be renamed without actually doing it
    """
    print("=== PREVIEW MODE ===")
    root_path = Path(root_dir)
    print(root_path)
    for movie_dir in root_path.iterdir():
        print(movie_dir)
        if movie_dir.is_dir():
            srt_files = []
            for file_path in movie_dir.iterdir():
                if (file_path.is_file() and 
                    file_path.suffix.lower() == '.srt' and 
                    not any(part in ['persian', 'archive'] for part in file_path.parts)):
                    srt_files.append(file_path.name)
            
            if srt_files:
                print(f"{movie_dir.name}:")
                for srt_file in srt_files:
                    print(f"  → {srt_file} -> english_subtitle.srt")

if __name__ == "__main__":
    # Set your directory path here (or use current directory)
    target_directory = "."  # Current directory
    
    # First, preview what will happen
    preview_changes(target_directory)
    
    # Ask for confirmation
    response = input("\nDo you want to proceed with renaming? (y/n): ")
    
    if response.lower() == 'y':
        print("\n=== STARTING RENAME OPERATION ===")
        rename_english_subtitles(target_directory)
        print("\n=== OPERATION COMPLETE ===")
    else:
        print("Operation cancelled.")