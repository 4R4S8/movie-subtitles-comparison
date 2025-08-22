#!/usr/bin/env python3
"""
Subtitle Comparison Visualizer
Standalone tool to create visualizations from subtitle comparison CSV files
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import json
import argparse
from datetime import datetime
import sys

# Set style
plt.style.use('default')
sns.set_palette("husl")

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles numpy data types"""
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)

def create_html_dashboard(csv_file, output_dir=None):
    """Create comprehensive HTML dashboard with interactive features"""
    try:
        df = pd.read_csv(csv_file)
        
        # Convert numpy types to native Python types for JSON serialization
        df = df.applymap(lambda x: convert_numpy_types(x))
        
        if output_dir is None:
            output_dir = Path(csv_file).parent
        
        output_html = output_dir / f"{Path(csv_file).stem}_dashboard.html"
        
        # Get Persian columns
        persian_cols = [col for col in df.columns if col not in ['Start Time', 'End Time', 'English']]
        
        # Calculate statistics
        stats = calculate_statistics(df, persian_cols)
        
        # Generate HTML content
        html_content = generate_html_template(df, persian_cols, stats, Path(csv_file).stem)
        
        # Write HTML file
        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML dashboard created: {output_html}")
        return output_html
        
    except Exception as e:
        print(f"❌ Error creating HTML dashboard: {e}")
        import traceback
        traceback.print_exc()
        return None

def convert_numpy_types(obj):
    """Convert numpy types to native Python types"""
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    elif isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    else:
        return str(obj)

def calculate_statistics(df, persian_cols):
    """Calculate comprehensive statistics"""
    stats = {
        'total_subtitles': len(df),
        'total_english_chars': int(df['English'].str.len().sum()) if 'English' in df.columns else 0,
        'files_compared': len(persian_cols),
        'coverage': {},
        'unique_translations': {},
        'avg_length': {},
        'divergence_scores': {}
    }
    
    for col in persian_cols:
        # Coverage
        non_empty = df[col].notna().sum()
        stats['coverage'][col] = float((non_empty / len(df)) * 100)
        
        # Unique translations
        stats['unique_translations'][col] = int(df[col].nunique())
        
        # Average length
        if df[col].notna().any():
            avg_len = df[col].str.len().mean()
            stats['avg_length'][col] = float(avg_len) if not pd.isna(avg_len) else 0.0
        else:
            stats['avg_length'][col] = 0.0
        
        # Divergence score (how different from others)
        divergence = 0.0
        valid_comparisons = 0
        for other_col in persian_cols:
            if other_col != col:
                matches = (df[col] == df[other_col]) & df[col].notna() & df[other_col].notna()
                if matches.any():
                    divergence += (1 - matches.mean()) * 100
                    valid_comparisons += 1
        
        if valid_comparisons > 0:
            stats['divergence_scores'][col] = float(divergence / valid_comparisons)
        else:
            stats['divergence_scores'][col] = 0.0
    
    # Convert all values to native Python types
    for key in stats:
        if isinstance(stats[key], dict):
            for subkey in stats[key]:
                stats[key][subkey] = convert_numpy_types(stats[key][subkey])
        else:
            stats[key] = convert_numpy_types(stats[key])
    
    return stats

def generate_html_template(df, persian_cols, stats, title):
    """Generate the HTML template with data"""
    # Convert data to JSON for JavaScript with proper encoding
    subtitle_data = []
    for _, row in df.iterrows():
        item = {}
        for col in df.columns:
            value = row[col]
            if pd.isna(value):
                item[col] = None
            else:
                item[col] = convert_numpy_types(value)
        subtitle_data.append(item)
    
    # Ensure all stats values are serializable
    serializable_stats = {}
    for key, value in stats.items():
        if isinstance(value, dict):
            serializable_stats[key] = {k: convert_numpy_types(v) for k, v in value.items()}
        else:
            serializable_stats[key] = convert_numpy_types(value)
    
    # Generate Persian columns HTML
    persian_html = ""
    for col in persian_cols:
        persian_html += f"""
        <div class="persian-text mb-1">
            <strong>🇮🇷 {col}:</strong> ${{item['{col}'] || '<em class="text-muted">Missing</em>'}}
        </div>
        """
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Subtitle Comparison - {title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f8f9fa; }}
        .dashboard-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
        .subtitle-card {{ 
            border-left: 4px solid #007bff; 
            transition: all 0.3s ease;
            background: white;
        }}
        .subtitle-card:hover {{ 
            transform: translateX(5px); 
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .subtitle-different {{ border-left-color: #ffc107; background: #fff3cd; }}
        .subtitle-missing {{ border-left-color: #dc3545; background: #f8d7da; }}
        .english-text {{ color: #2c3e50; font-weight: 500; }}
        .persian-text {{ color: #2980b9; direction: rtl; text-align: right; }}
        .time-badge {{ background: #6c757d; font-size: 0.8em; }}
        .stats-card {{ background: white; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .chart-container {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; }}
        .highlight {{ background: #ffeb3b !important; }}
    </style>
</head>
<body>
    <div class="dashboard-header py-4 mb-4">
        <div class="container">
            <h1 class="display-4">🎬 Subtitle Comparison Dashboard</h1>
            <p class="lead">Analysis of {title} - {stats['total_subtitles']} subtitles compared</p>
        </div>
    </div>

    <div class="container">
        <!-- Controls -->
        <div class="row mb-4">
            <div class="col">
                <div class="card">
                    <div class="card-body">
                        <div class="row g-3 align-items-center">
                            <div class="col-md-4">
                                <input type="text" id="searchBox" class="form-control" 
                                       placeholder="🔍 Search across all translations...">
                            </div>
                            <div class="col-md-8">
                                <div class="btn-group">
                                    <button onclick="highlightDifferences()" class="btn btn-warning">
                                        ⚡ Highlight Differences
                                    </button>
                                    <button onclick="showAll()" class="btn btn-secondary">
                                        🔄 Show All
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Statistics -->
        <div class="row mb-4">
            <div class="col">
                <div class="stats-card p-4">
                    <h3>📊 Overall Statistics</h3>
                    <div class="row">
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4>{stats['total_subtitles']}</h4>
                                <small>Total Subtitles</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4>{stats['files_compared']}</h4>
                                <small>Files Compared</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4>{stats['total_english_chars']:,}</h4>
                                <small>Total English Characters</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- File Statistics -->
        <div class="row mb-4">
            <div class="col">
                <div class="stats-card p-4">
                    <h5>📋 File Comparison Details</h5>
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>File</th>
                                    <th>Coverage</th>
                                    <th>Unique Translations</th>
                                    <th>Avg Length</th>
                                    <th>Divergence</th>
                                </tr>
                            </thead>
                            <tbody>
                                {"".join([f"""
                                <tr>
                                    <td>{col}</td>
                                    <td>{stats['coverage'].get(col, 0):.1f}%</td>
                                    <td>{stats['unique_translations'].get(col, 0)}</td>
                                    <td>{stats['avg_length'].get(col, 0):.1f}</td>
                                    <td>{stats['divergence_scores'].get(col, 0):.1f}%</td>
                                </tr>
                                """ for col in persian_cols])}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- Subtitles -->
        <div class="row">
            <div class="col">
                <h4>🎭 Subtitle Comparisons</h4>
                <div id="subtitleContainer">
                    <!-- Subtitles will be inserted here -->
                </div>
            </div>
        </div>
    </div>

    <!-- JavaScript -->
    <script>
        const subtitleData = {json.dumps(subtitle_data, ensure_ascii=False, cls=NumpyEncoder)};
        const stats = {json.dumps(serializable_stats, ensure_ascii=False, cls=NumpyEncoder)};
        const persianCols = {json.dumps(persian_cols, ensure_ascii=False)};

        // Render functions
        function renderSubtitles(data) {{
            const container = document.getElementById('subtitleContainer');
            container.innerHTML = '';
            
            data.forEach((item, index) => {{
                const card = document.createElement('div');
                card.className = 'card subtitle-card mb-3';
                
                let persianContent = '';
                persianCols.forEach(col => {{
                    const value = item[col] || '<em class="text-muted">Missing</em>';
                    persianContent += `
                        <div class="persian-text mb-1">
                            <strong>🇮🇷 {col}:</strong> ${{value}}
                        </div>
                    `;
                }});
                
                card.innerHTML = `
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <span class="time-badge badge bg-secondary">⏰ ${{item['Start Time']}} - ${{item['End Time']}}</span>
                            <small class="text-muted">#${{index + 1}}</small>
                        </div>
                        <div class="english-text mb-2">🇺🇸 ${{item['English'] || 'No translation'}}</div>
                        ${{persianContent}}
                    </div>
                `;
                container.appendChild(card);
            }});
        }}

        function highlightDifferences() {{
            const cards = document.querySelectorAll('.subtitle-card');
            cards.forEach(card => {{
                const persianTexts = card.querySelectorAll('.persian-text');
                const texts = Array.from(persianTexts).map(el => 
                    el.textContent.replace(/^.*?:/, '').trim()
                );
                
                const hasContent = texts.some(text => text && !text.includes('Missing'));
                const allSame = texts.every((text, i, arr) => 
                    text === arr[0] || !text || text === 'Missing'
                );
                
                card.classList.remove('subtitle-different', 'subtitle-missing');
                if (!hasContent) {{
                    card.classList.add('subtitle-missing');
                }} else if (!allSame) {{
                    card.classList.add('subtitle-different');
                }}
            }});
        }}

        function searchSubtitles() {{
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            const filteredData = subtitleData.filter(item => 
                Object.values(item).some(value => 
                    value && value.toString().toLowerCase().includes(searchTerm)
                )
            );
            renderSubtitles(filteredData);
        }}

        function showAll() {{
            renderSubtitles(subtitleData);
            document.getElementById('searchBox').value = '';
            document.querySelectorAll('.subtitle-card').forEach(card => {{
                card.classList.remove('subtitle-different', 'subtitle-missing');
            }});
        }}

        // Event listeners
        document.getElementById('searchBox').addEventListener('input', searchSubtitles);
        
        // Initial render
        document.addEventListener('DOMContentLoaded', function() {{
            renderSubtitles(subtitleData);
        }});
    </script>
</body>
</html>
    """

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Subtitle Comparison Visualizer')
    parser.add_argument('csv_file', help='Input CSV file from subtitle comparison')
    parser.add_argument('--output-dir', '-o', help='Output directory (default: same as input)')
    
    args = parser.parse_args()
    
    if not Path(args.csv_file).exists():
        print(f"❌ CSV file not found: {args.csv_file}")
        sys.exit(1)
    
    print(f"📊 Processing: {args.csv_file}")
    
    # Create HTML dashboard
    html_path = create_html_dashboard(args.csv_file, args.output_dir)
    
    if html_path:
        print(f"\n🎉 Visualization complete!")
        print(f"   📈 HTML Dashboard: {html_path}")
        print(f"\n   Open the file in your web browser to view the interactive dashboard!")

if __name__ == "__main__":
    main()