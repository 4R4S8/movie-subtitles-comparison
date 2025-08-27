#!/usr/bin/env python3
"""
Recursive Subtitle Comparison Visualizer
Processes all JSON files in Data directory and creates side-by-side comparison views
"""

import json
import argparse
from pathlib import Path
import sys
from datetime import datetime

def find_json_files(data_dir):
    """Recursively find all JSON files in Data directory"""
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return []
    
    json_files = list(data_path.rglob("*_comparison.json"))
    print(f"📁 Found {len(json_files)} JSON files in {data_dir}")
    return json_files

def load_json_data(json_file):
    """Load JSON data from file"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading JSON file {json_file}: {e}")
        return None

def calculate_statistics(data):
    """Calculate statistics from JSON data"""
    if not data or 'subtitles' not in data:
        return None
    
    stats = {
        'total_subtitles': len(data['subtitles']),
        'files_compared': 0,
        'coverage': {},
        'file_mapping': data.get('file_mapping', {})
    }
    
    # Count files and calculate coverage
    for folder, files in stats['file_mapping'].items():
        for file_key in files:
            full_key = f"{folder}_{file_key}"
            translations_count = 0
            
            for subtitle in data['subtitles']:
                if (folder in subtitle['translations'] and 
                    file_key in subtitle['translations'][folder] and
                    subtitle['translations'][folder][file_key]):
                    translations_count += 1
            
            stats['coverage'][full_key] = (translations_count / stats['total_subtitles'] * 100) if stats['total_subtitles'] > 0 else 0
    
    stats['files_compared'] = sum(len(files) for files in stats['file_mapping'].values())
    return stats

def create_comparison_html(data, output_file, movie_name):
    """Create HTML with side-by-side comparison layout"""
    if not data or 'subtitles' not in data:
        return False
    
    stats = calculate_statistics(data)
    if not stats:
        return False
    
    # Generate HTML content
    html_content = generate_comparison_html(data, stats, movie_name)
    
    # Write HTML file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return True
    except Exception as e:
        print(f"❌ Error writing HTML file {output_file}: {e}")
        return False

def generate_comparison_html(data, stats, movie_name):
    """Generate side-by-side comparison HTML"""
    
    # File mapping section
    file_mapping_html = ""
    for folder, files in stats['file_mapping'].items():
        file_mapping_html += f"""
        <div class="mb-2">
            <strong>{folder}/</strong>
            <div style="margin-left: 20px;">
        """
        for file_key, file_name in files.items():
            coverage = stats['coverage'].get(f"{folder}_{file_key}", 0)
            file_mapping_html += f"""
                <div>📄 {file_key} → {file_name} 
                    <small>({coverage:.1f}% coverage)</small>
                </div>
            """
        file_mapping_html += "</div></div>"
    
    # Statistics section
    stats_html = f"""
    <div class="row text-center mb-4">
        <div class="col-md-3">
            <div class="stat-card bg-primary text-white p-3 rounded">
                <h4>{stats['total_subtitles']}</h4>
                <small>Total Subtitles</small>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card bg-success text-white p-3 rounded">
                <h4>{stats['files_compared']}</h4>
                <small>Files Compared</small>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card bg-info text-white p-3 rounded">
                <h4>{datetime.now().strftime('%Y-%m-%d')}</h4>
                <small>Generated</small>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card bg-warning text-white p-3 rounded">
                <h4>{movie_name}</h4>
                <small>Movie</small>
            </div>
        </div>
    </div>
    """
    
    # Group translations by folder
    subkade_translations = {}
    opensubtitle_translations = {}
    other_translations = {}
    
    for folder, files in stats['file_mapping'].items():
        if 'subkade' in folder.lower():
            subkade_translations = files
        elif 'opensubtitle' in folder.lower():
            opensubtitle_translations = files
        else:
            other_translations[folder] = files
    
    # Comparison table header
    comparison_header = """
    <div class="comparison-table mt-4">
        <div class="row comparison-header bg-dark text-white p-2">
            <div class="col-md-2 text-center">
                <strong>Time</strong>
            </div>
            <div class="col-md-3 text-center">
                <strong>🇺🇸 English</strong>
            </div>
            <div class="col-md-3 text-center">
                <strong>🇮🇷 Subkade</strong>
            </div>
            <div class="col-md-3 text-center">
                <strong>🇮🇷 OpenSubtitles</strong>
            </div>
            <div class="col-md-1 text-center">
                <strong>#</strong>
            </div>
        </div>
    """
    
    # Subtitles comparison rows
    comparison_rows = ""
    for i, subtitle in enumerate(data['subtitles']):
        start_time, end_time = subtitle['time'].split(',')
        english_text = subtitle['english'] or "No translation"
        
        # Get Subkade translations
        subkade_texts = []
        for file_key in subkade_translations:
            if ('subkade' in subtitle['translations'] and 
                file_key in subtitle['translations']['subkade']):
                trans = subtitle['translations']['subkade'][file_key]
                if trans:
                    subkade_texts.append(f"<div class='persian-text'>{trans}</div>")
        
        subkade_html = "<br>".join(subkade_texts) if subkade_texts else "<em class='text-muted'>No translation</em>"
        
        # Get OpenSubtitles translations
        opensubtitle_texts = []
        for file_key in opensubtitle_translations:
            if ('opensubtitle' in subtitle['translations'] and 
                file_key in subtitle['translations']['opensubtitle']):
                trans = subtitle['translations']['opensubtitle'][file_key]
                if trans:
                    opensubtitle_texts.append(f"<div class='persian-text'>{trans}</div>")
        
        opensubtitle_html = "<br>".join(opensubtitle_texts) if opensubtitle_texts else "<em class='text-muted'>No translation</em>"
        
        comparison_rows += f"""
        <div class="row comparison-row p-2 {'bg-light' if i % 2 == 0 else ''}">
            <div class="col-md-2">
                <small class="text-muted">{start_time}<br>{end_time}</small>
            </div>
            <div class="col-md-3 english-text">
                {english_text}
            </div>
            <div class="col-md-3 persian-text">
                {subkade_html}
            </div>
            <div class="col-md-3 persian-text">
                {opensubtitle_html}
            </div>
            <div class="col-md-1 text-center">
                <small class="text-muted">{i+1}</small>
            </div>
        </div>
        """
    
    comparison_footer = "</div>"
    
    # Full HTML template
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Subtitle Comparison - {movie_name}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: #f8f9fa; 
            padding-bottom: 50px;
        }}
        .dashboard-header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            margin-bottom: 30px;
        }}
        .english-text {{ 
            color: #2c3e50; 
            font-weight: 500; 
            line-height: 1.4;
        }}
        .persian-text {{ 
            color: #2980b9; 
            direction: rtl; 
            text-align: right; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
        }}
        .comparison-header {{
            font-weight: bold;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .comparison-row {{
            border-bottom: 1px solid #eee;
            transition: background-color 0.2s ease;
        }}
        .comparison-row:hover {{
            background-color: #e3f2fd !important;
        }}
        .stat-card {{
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }}
        .stat-card:hover {{
            transform: translateY(-2px);
        }}
        .file-mapping {{ 
            background: #e9ecef; 
            padding: 15px; 
            border-radius: 8px; 
            font-size: 0.9em; 
        }}
        .nav-buttons {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
        }}
    </style>
</head>
<body>
    <div class="dashboard-header py-4">
        <div class="container">
            <h1 class="display-4">🎬 Subtitle Comparison Dashboard</h1>
            <p class="lead">Side-by-side comparison for {movie_name}</p>
        </div>
    </div>

    <div class="container">
        <!-- File Mapping -->
        <div class="row mb-4">
            <div class="col">
                <div class="card">
                    <div class="card-header">
                        <h5>📁 File Mapping</h5>
                    </div>
                    <div class="card-body file-mapping">
                        {file_mapping_html}
                    </div>
                </div>
            </div>
        </div>

        <!-- Statistics -->
        <div class="row mb-4">
            <div class="col">
                <div class="card">
                    <div class="card-header">
                        <h5>📊 Statistics</h5>
                    </div>
                    <div class="card-body">
                        {stats_html}
                    </div>
                </div>
            </div>
        </div>

        <!-- Comparison Table -->
        <div class="row">
            <div class="col">
                <h4 class="mb-3">🎭 Side-by-Side Comparison</h4>
                {comparison_header}
                {comparison_rows}
                {comparison_footer}
            </div>
        </div>
    </div>

    <!-- Navigation Buttons -->
    <div class="nav-buttons">
        <button onclick="scrollToTop()" class="btn btn-primary rounded-circle shadow" 
                style="width: 50px; height: 50px; margin-right: 10px;">
            ↑
        </button>
        <button onclick="scrollToBottom()" class="btn btn-secondary rounded-circle shadow" 
                style="width: 50px; height: 50px;">
            ↓
        </button>
    </div>

    <!-- JavaScript -->
    <script>
        function scrollToTop() {{
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}

        function scrollToBottom() {{
            window.scrollTo({{ top: document.body.scrollHeight, behavior: 'smooth' }});
        }}

        // Add search functionality
        function addSearch() {{
            const searchDiv = document.createElement('div');
            searchDiv.className = 'row mb-4';
            searchDiv.innerHTML = `
                <div class="col">
                    <div class="card">
                        <div class="card-body">
                            <input type="text" id="searchBox" class="form-control" 
                                   placeholder="🔍 Search across all translations..." 
                                   oninput="filterSubtitles()">
                            <small class="text-muted">Search in English or Persian text</small>
                        </div>
                    </div>
                </div>
            `;
            
            const statsCard = document.querySelector('.card .card-body');
            statsCard.parentNode.insertBefore(searchDiv, statsCard.nextSibling);
        }}

        function filterSubtitles() {{
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            const rows = document.querySelectorAll('.comparison-row');
            
            rows.forEach(row => {{
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {{
                    row.style.display = 'flex';
                    row.style.backgroundColor = '#fff3cd';
                }} else {{
                    row.style.display = 'none';
                }}
            }});
        }}

        function showAll() {{
            const rows = document.querySelectorAll('.comparison-row');
            rows.forEach(row => {{
                row.style.display = 'flex';
                row.style.backgroundColor = '';
            }});
        }}

        // Initialize search on page load
        document.addEventListener('DOMContentLoaded', function() {{
            addSearch();
        }});
    </script>
</body>
</html>
    """

def process_all_json_files(data_dir, output_dir=None):
    """Process all JSON files in Data directory"""
    json_files = find_json_files(data_dir)
    if not json_files:
        print("❌ No JSON files found to process")
        return
    
    successful = 0
    failed = 0
    
    for json_file in json_files:
        print(f"\n📊 Processing: {json_file.name}")
        
        # Determine output directory
        if output_dir:
            movie_output_dir = Path(output_dir) / json_file.parent.name
            movie_output_dir.mkdir(parents=True, exist_ok=True)
            output_html = movie_output_dir / f"{json_file.stem}_dashboard.html"
        else:
            output_html = json_file.parent / f"{json_file.stem}_dashboard.html"
        
        # Load data and create HTML
        data = load_json_data(json_file)
        if data:
            success = create_comparison_html(data, output_html, json_file.parent.name)
            if success:
                print(f"✅ Created: {output_html}")
                successful += 1
            else:
                print(f"❌ Failed to create HTML for {json_file.name}")
                failed += 1
        else:
            failed += 1
    
    print(f"\n🎉 Processing complete!")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📊 Total: {len(json_files)}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Recursive Subtitle Comparison Visualizer')
    parser.add_argument('--data-dir', '-d', default='Data', help='Data directory (default: Data)')
    parser.add_argument('--output-dir', '-o', help='Output directory (default: same as input)')
    
    args = parser.parse_args()
    
    print("🚀 Starting recursive subtitle comparison processing...")
    print("=" * 60)
    
    process_all_json_files(args.data_dir, args.output_dir)

if __name__ == "__main__":
    main()