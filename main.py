#!/usr/bin/env python3
"""
PlaylistTagger - CSV Edition
Builds personal music libraries from CSV playlists with rich metadata.

Author: PlaylistTagger Team
Python: 3.10+
"""

import os
import re
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
import yt_dlp
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC
from mutagen.mp3 import MP3
from tqdm import tqdm


# ============================================================================
# Configuration
# ============================================================================

DOWNLOADS_FOLDER = "downloads"
FAILED_LOG = "failed_log.txt"
SUMMARY_LOG = "summary_log.txt"
AUDIO_QUALITY = "192"  # kbps CBR


# ============================================================================
# Utilities
# ============================================================================

def sanitize_filename(text: str) -> str:
    """
    Sanitize text for safe filesystem usage.
    Removes/replaces invalid characters for cross-platform compatibility.
    """
    # Remove invalid filesystem characters
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def create_downloads_folder() -> None:
    """Create downloads folder if it doesn't exist."""
    Path(DOWNLOADS_FOLDER).mkdir(exist_ok=True)


def file_exists(artist: str, track: str) -> bool:
    """
    Smart Skip: Check if the MP3 file already exists.
    
    Args:
        artist: Artist name
        track: Track name
        
    Returns:
        True if file exists, False otherwise
    """
    filename = f"{sanitize_filename(artist)} - {sanitize_filename(track)}.mp3"
    filepath = Path(DOWNLOADS_FOLDER) / filename
    return filepath.exists()


def log_failure(artist: str, track: str, error: str) -> None:
    """
    Log failed download to failed_log.txt.
    
    Args:
        artist: Artist name
        track: Track name
        error: Error message
    """
    with open(FAILED_LOG, "a", encoding="utf-8") as f:
        f.write(f"{artist} - {track}: {error}\n")


# ============================================================================
# CSV Validation and Column Mapping
# ============================================================================

def validate_and_fix_csv(csv_path: str) -> pd.DataFrame:
    """
    Validate CSV file and automatically fix column name variations.
    
    This function:
    1. Reads the CSV file
    2. Checks for required columns
    3. Maps common column name variations to expected names
    4. Shows detailed logs of what was found and fixed
    5. Returns a DataFrame ready for processing
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        Validated and fixed DataFrame
        
    Raises:
        SystemExit: If CSV cannot be read or critical columns are missing
    """
    print("\n" + "=" * 50)
    print("📋 CSV Validation & Column Mapping")
    print("=" * 50)
    
    # Load CSV
    try:
        df = pd.read_csv(csv_path)
        print(f"✓ CSV loaded successfully: {len(df)} rows found")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        sys.exit(1)
    
    # Define expected columns and their common variations
    column_mappings = {
        'Track Name': [
            'Track Name', 'track_name', 'TrackName', 'track name',
            'Song Name', 'song_name', 'Title', 'title', 'Song', 'Track'
        ],
        'Artist Name': [
            'Artist Name', 'Artist Name(s)', 'artist_name', 'ArtistName',
            'artist name', 'Artist', 'artist', 'Artists', 'Artist(s)'
        ],
        'Album Name': [
            'Album Name', 'album_name', 'AlbumName', 'album name',
            'Album', 'album'
        ],
        'Album Image URL': [
            'Album Image URL', 'album_image_url', 'AlbumImageURL',
            'Album Image', 'album image', 'Cover Art', 'cover_art',
            'Image URL', 'image_url', 'Cover', 'ImageURL'
        ]
    }
    
    # Display current columns
    print(f"\n📊 Current CSV Columns ({len(df.columns)} total):")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col}")
    
    # Column mapping results
    print("\n🔍 Column Mapping Results:")
    print("-" * 50)
    
    mapping_performed = {}
    missing_columns = []
    
    # Check and map each required column
    for expected_col, variations in column_mappings.items():
        found = False
        
        # Check if any variation exists in the CSV
        for variation in variations:
            if variation in df.columns:
                if variation != expected_col:
                    # Rename column
                    df.rename(columns={variation: expected_col}, inplace=True)
                    mapping_performed[variation] = expected_col
                    print(f"✓ '{variation}' → '{expected_col}' (renamed)")
                else:
                    print(f"✓ '{expected_col}' (already correct)")
                found = True
                break
        
        if not found:
            missing_columns.append(expected_col)
            print(f"❌ '{expected_col}' NOT FOUND")
    
    # Summary
    print("\n" + "=" * 50)
    print("📝 Validation Summary:")
    print("=" * 50)
    
    if mapping_performed:
        print(f"✓ Renamed {len(mapping_performed)} column(s)")
        for old, new in mapping_performed.items():
            print(f"  • {old} → {new}")
    else:
        print("✓ All columns already have correct names")
    
    if missing_columns:
        print(f"\n❌ CRITICAL: Missing required columns:")
        for col in missing_columns:
            print(f"  • {col}")
        print("\n⚠️  Cannot proceed without these columns!")
        print("Please ensure your CSV has columns matching these variations:")
        for col in missing_columns:
            print(f"\n  {col}:")
            for variation in column_mappings[col]:
                print(f"    - {variation}")
        sys.exit(1)
    
    # Validate data quality
    print("\n🔍 Data Quality Check:")
    print("-" * 50)
    
    required_columns = ['Track Name', 'Artist Name']
    empty_counts = {}
    
    for col in required_columns:
        empty_count = df[col].isna().sum() + (df[col] == '').sum()
        empty_counts[col] = empty_count
        
        if empty_count > 0:
            print(f"⚠️  '{col}': {empty_count} empty row(s) found (will be skipped)")
        else:
            print(f"✓ '{col}': All rows have data")
    
    # Show optional column status
    optional_columns = ['Album Name', 'Album Image URL']
    for col in optional_columns:
        empty_count = df[col].isna().sum() + (df[col] == '').sum()
        if empty_count > 0:
            print(f"ℹ️  '{col}': {empty_count} empty row(s) (optional, will use defaults)")
        else:
            print(f"✓ '{col}': All rows have data")
    
    print("\n" + "=" * 50)
    print("✅ CSV Validation Complete!")
    print(f"✅ Ready to process {len(df)} tracks")
    print("=" * 50 + "\n")
    
    return df


# ============================================================================
# YouTube Download
# ============================================================================

def download_from_youtube(artist: str, track: str) -> Optional[str]:
    """
    Search YouTube and download audio as MP3.
    
    Args:
        artist: Artist name
        track: Track name
        
    Returns:
        Path to downloaded MP3 file, or None if failed
    """
    try:
        # Construct search query
        search_query = f"ytsearch1:{artist} - {track} audio"
        
        # Sanitized filename for output
        filename = f"{sanitize_filename(artist)} - {sanitize_filename(track)}"
        output_path = str(Path(DOWNLOADS_FOLDER) / filename)
        
        # yt-dlp configuration
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': AUDIO_QUALITY,
            }],
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,  # Continue on errors
        }
        
        # Download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(search_query, download=True)
            
            # Check if download was successful
            if result is None:
                return None
                
        return f"{output_path}.mp3"
        
    except Exception as e:
        log_failure(artist, track, f"YouTube download error: {str(e)}")
        return None


# ============================================================================
# Metadata Embedding (The Critical Part)
# ============================================================================

def download_cover_art(image_url: str) -> Optional[str]:
    """
    Download album cover art image temporarily.
    
    Args:
        image_url: URL to album image
        
    Returns:
        Path to temporary image file, or None if failed
    """
    if not image_url or pd.isna(image_url):
        return None
        
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Save temporarily
        temp_image_path = "temp_cover.jpg"
        with open(temp_image_path, "wb") as f:
            f.write(response.content)
            
        return temp_image_path
        
    except Exception:
        # Silently fail - we'll continue without cover art
        return None


def embed_metadata(
    mp3_path: str,
    title: str,
    artist: str,
    album: str,
    cover_art_path: Optional[str] = None
) -> bool:
    """
    Embed ID3 tags and cover art into MP3 file.
    
    This is the "Metadata Bridge" - we take data from the CSV
    (which came from Spotify export) and stamp it onto the YouTube audio,
    creating a properly tagged music file.
    
    Args:
        mp3_path: Path to MP3 file
        title: Track title
        artist: Artist name
        album: Album name
        cover_art_path: Optional path to cover art image
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Load or create ID3 tags
        try:
            audio = MP3(mp3_path, ID3=ID3)
            audio.add_tags()
        except Exception:
            audio = MP3(mp3_path)
            
        # Embed text metadata
        audio.tags.add(TIT2(encoding=3, text=title))      # Title
        audio.tags.add(TPE1(encoding=3, text=artist))     # Artist
        audio.tags.add(TALB(encoding=3, text=album))      # Album
        
        # Embed cover art (APIC frame) if available
        if cover_art_path and Path(cover_art_path).exists():
            try:
                with open(cover_art_path, "rb") as img_file:
                    audio.tags.add(
                        APIC(
                            encoding=3,                    # UTF-8
                            mime='image/jpeg',             # MIME type
                            type=3,                        # Cover (front)
                            desc='Cover',
                            data=img_file.read()
                        )
                    )
            except Exception:
                # Continue without cover art if it fails
                pass
                
        # Save changes
        audio.save()
        return True
        
    except Exception as e:
        return False


# ============================================================================
# Main Processing Loop
# ============================================================================

def process_playlist(csv_path: str) -> dict:
    """
    Main processing loop: reads CSV and downloads songs with metadata.
    
    Args:
        csv_path: Path to playlist CSV file
        
    Returns:
        Dictionary with statistics (processed, skipped, failed)
    """
    # Validate and fix CSV columns
    df = validate_and_fix_csv(csv_path)
        
    # Statistics counters
    stats = {
        'processed': 0,
        'skipped': 0,
        'failed': 0
    }
    
    # Progress bar
    with tqdm(total=len(df), desc="Processing songs", unit="song") as pbar:
        for _, row in df.iterrows():
            track = row['Track Name']
            artist = row['Artist Name']
            album = row['Album Name']
            image_url = row['Album Image URL']
            
            # Update progress bar with current song
            pbar.set_description(f"Processing: {artist} - {track}")
            
            # Smart Skip: Check if file already exists
            if file_exists(artist, track):
                print(f"✓ Already exists: {artist} - {track}")
                stats['skipped'] += 1
                pbar.update(1)
                continue
                
            # Download from YouTube
            mp3_path = download_from_youtube(artist, track)
            if not mp3_path:
                log_failure(artist, track, "YouTube search returned no results")
                stats['failed'] += 1
                pbar.update(1)
                continue
                
            # Download cover art (optional)
            cover_art_path = download_cover_art(image_url)
            
            # Embed metadata (The Critical Part)
            success = embed_metadata(mp3_path, track, artist, album, cover_art_path)
            
            # Cleanup temporary cover art
            if cover_art_path and Path(cover_art_path).exists():
                try:
                    Path(cover_art_path).unlink()
                except Exception:
                    pass
                    
            if success:
                stats['processed'] += 1
            else:
                log_failure(artist, track, "Metadata embedding failed")
                stats['failed'] += 1
                
            pbar.update(1)
            
    return stats


def write_summary(stats: dict) -> None:
    """
    Write summary statistics to summary_log.txt.
    
    Args:
        stats: Dictionary with statistics
    """
    with open(SUMMARY_LOG, "w", encoding="utf-8") as f:
        f.write("=" * 50 + "\n")
        f.write("PlaylistTagger - Processing Summary\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total Processed: {stats['processed']}\n")
        f.write(f"Total Skipped (Existing): {stats['skipped']}\n")
        f.write(f"Total Failed: {stats['failed']}\n\n")
        f.write("=" * 50 + "\n")


# ============================================================================
# Entry Point
# ============================================================================

def main():
    """Main entry point."""
    print("🎵 PlaylistTagger - CSV Edition")
    print("=" * 50)
    
    # Setup
    create_downloads_folder()
    
    # Check if playlist.csv exists
    if not Path("playlist.csv").exists():
        print("❌ Error: playlist.csv not found!")
        print("Please create a playlist.csv file with your music data.")
        sys.exit(1)
        
    # Process playlist
    stats = process_playlist("playlist.csv")
    
    # Write summary
    write_summary(stats)
    
    # Final report
    print("\n" + "=" * 50)
    print("✅ Processing Complete!")
    print("=" * 50)
    print(f"Processed: {stats['processed']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Failed: {stats['failed']}")
    print(f"\nSummary saved to: {SUMMARY_LOG}")
    if stats['failed'] > 0:
        print(f"Failed songs logged to: {FAILED_LOG}")


if __name__ == "__main__":
    main()
