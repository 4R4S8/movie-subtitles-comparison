import os
import shutil
from pathlib import Path

def rename_english_to_persian(root_dir='.'):
    """Rename all 'english' folders to 'persian'"""
    root_path = Path(root_dir)
    
    for english_dir in root_path.glob('**/english'):
        persian_dir = english_dir.parent / 'persian'
        
        if english_dir.exists() and not persian_dir.exists():
            english_dir.rename(persian_dir)
            print(f"Renamed {english_dir} to {persian_dir}")
        elif persian_dir.exists():
            print(f"Persian folder already exists: {persian_dir}")

def move_zips_to_archive(root_dir='.'):
    """Move all zip files to an 'archive' folder in their parent directory"""
    root_path = Path(root_dir)
    
    for zip_path in root_path.glob('**/*.zip'):
        # Skip files already in archive folders
        if 'archive' in zip_path.parts:
            continue
            
        parent_dir = zip_path.parent
        archive_dir = parent_dir / 'archive'
        
        # Create archive directory if it doesn't exist
        archive_dir.mkdir(exist_ok=True)
        
        target_path = archive_dir / zip_path.name
        if not target_path.exists():
            shutil.move(str(zip_path), str(target_path))
            print(f"Moved {zip_path} to {target_path}")
        else:
            print(f"Zip already exists in archive: {target_path}")

def flatten_persian_folders(root_dir='.'):
    """Flatten persian folder structure (move all files to root of persian folder)"""
    root_path = Path(root_dir)
    
    for persian_dir in root_path.glob('**/persian'):  # Note: Fixed typo from 'persian' to 'persian'
        if not persian_dir.exists():
            continue
            
        # First collect all files to move (to avoid modifying while iterating)
        files_to_move = []
        for file_path in persian_dir.rglob('*'):
            if file_path.is_file() and file_path.parent != persian_dir:
                files_to_move.append(file_path)
        
        # Now move them
        for file_path in files_to_move:
            target_path = persian_dir / file_path.name
            
            # Handle duplicate filenames
            if target_path.exists():
                stem = file_path.stem
                suffix = file_path.suffix
                counter = 1
                while target_path.exists():
                    target_path = persian_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
            
            shutil.move(str(file_path), str(target_path))
            print(f"Moved {file_path} to {target_path}")
        
        # Remove empty subdirectories (bottom-up)
        for sub_dir in sorted(persian_dir.glob('*/'), key=lambda p: len(p.parts), reverse=True):
            try:
                sub_dir.rmdir()
                print(f"Removed empty directory: {sub_dir}")
            except OSError:
                # Directory not empty or other error
                pass

if __name__ == '__main__':
    print("=== Renaming english folders to persian ===")
    rename_english_to_persian()  # Fixed function name
    
    print("\n=== Moving zip files to archive folders ===")
    move_zips_to_archive()
    
    print("\n=== Flattening persian folder structures ===")
    flatten_persian_folders()
    
    print("\nOperation completed!")