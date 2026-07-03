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
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
import yt_dlp
# pyrefly: ignore [missing-import]
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, TRCK, TPOS, TSRC
# pyrefly: ignore [missing-import]
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
    # Required columns first, then optional
    column_mappings = {
        # ── Required ──────────────────────────────────────────────────────────
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
        ],
        # ── Optional (enriched Spotify fields) ────────────────────────────────
        'Track Duration (ms)': [
            'Track Duration (ms)', 'Duration (ms)', 'duration_ms',
            'Duration', 'Track Duration', 'duration'
        ],
        'ISRC': [
            'ISRC', 'isrc', 'Track ISRC'
        ],
        'Track Number': [
            'Track Number', 'track_number', 'TrackNumber', 'track number'
        ],
        'Disc Number': [
            'Disc Number', 'disc_number', 'DiscNumber', 'disc number'
        ],
        'Album Artist Name': [
            'Album Artist Name(s)', 'Album Artist Name', 'album_artist',
            'AlbumArtist', 'Album Artist'
        ],
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
    
    # Separate required from optional for error reporting
    REQUIRED_COLS = {'Track Name', 'Artist Name', 'Album Name', 'Album Image URL'}
    critical_missing = [c for c in missing_columns if c in REQUIRED_COLS]
    if critical_missing:
        print(f"\n❌ CRITICAL: Missing required columns:")
        for col in critical_missing:
            print(f"  • {col}")
        print("\n⚠️  Cannot proceed without these columns!")
        print("Please ensure your CSV has columns matching these variations:")
        for col in critical_missing:
            print(f"\n  {col}:")
            for variation in column_mappings[col]:
                print(f"    - {variation}")
        sys.exit(1)
    if missing_columns:
        print(f"ℹ️  Optional columns not found (will use defaults): {missing_columns}")
    
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
    optional_columns = ['Album Name', 'Album Image URL', 'ISRC', 'Track Duration (ms)',
                        'Track Number', 'Disc Number', 'Album Artist Name']
    for col in optional_columns:
        if col not in df.columns:
            continue
        empty_count = df[col].isna().sum() + (df[col] == '').sum()
        if empty_count > 0:
            print(f"ℹ️  '{col}': {empty_count} empty row(s) (optional, will use defaults)")
        else:
            print(f"✓ '{col}': All rows have data ({len(df)} rows)")
    
    print("\n" + "=" * 50)
    print("✅ CSV Validation Complete!")
    print(f"✅ Ready to process {len(df)} tracks")
    print("=" * 50 + "\n")
    
    return df


# ============================================================================
# YouTube Download
# ============================================================================

# Minimum integrity score (0.0–1.0) required to accept a candidate.
# Raise this to be stricter; lower if too many songs are skipped.
MIN_INTEGRITY_SCORE = 0.35

# Number of YouTube candidates to evaluate per search attempt.
CANDIDATE_COUNT = 5

# Penalty keywords in YouTube titles that indicate wrong version.
BAD_KEYWORDS = [
    'cover', 'karaoke', 'tribute', 'instrumental', 'remix',
    'live', 'acoustic', 'piano', 'nightcore', 'sped up', 'slowed',
    'reaction', 'tutorial', 'mashup', 'parody', 'amv', 'wmv'
]


def _text_similarity(a: str, b: str) -> float:
    """Case-insensitive fuzzy similarity ratio between two strings."""
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _score_candidate(
    entry: dict,
    artist: str,
    track: str,
    duration_ms: Optional[int] = None
) -> float:
    """
    Score a YouTube search result for how well it matches the target song.

    Scoring breakdown (max 1.0):
      - Title similarity to '<artist> - <track>':  0.50 weight
      - Artist name present in uploader/channel:   0.20 weight
      - Duration proximity (if duration_ms given):  0.25 weight
      - Bad-keyword penalty:                       -0.30 per keyword hit

    Args:
        entry:       yt-dlp info dict for a single result.
        artist:      Expected artist name from CSV.
        track:       Expected track name from CSV.
        duration_ms: Expected duration in milliseconds (optional).

    Returns:
        Score float in range [0.0, 1.0].
    """
    yt_title = entry.get('title', '') or ''
    uploader = entry.get('uploader', '') or ''
    channel = entry.get('channel', '') or ''
    yt_duration = entry.get('duration')  # seconds, may be None

    # 1. Title similarity: compare YT title against "Artist - Track"
    expected_full = f"{artist} - {track}"
    title_score = max(
        _text_similarity(yt_title, expected_full),
        _text_similarity(yt_title, track),          # sometimes YT drops artist
    )

    # 2. Artist name presence in uploader / channel / title
    artist_lower = artist.lower()
    artist_hits = (
        artist_lower in uploader.lower()
        or artist_lower in channel.lower()
        or artist_lower in yt_title.lower()
    )
    artist_score = 1.0 if artist_hits else 0.0

    # 3. Duration proximity (only when CSV provides it)
    duration_score = 0.0
    if duration_ms and yt_duration:
        expected_sec = duration_ms / 1000.0
        diff_ratio = abs(yt_duration - expected_sec) / max(expected_sec, 1)
        # Perfect match → 1.0; ±5 % → ~0.95; ±50 % → 0.0
        duration_score = max(0.0, 1.0 - diff_ratio * 2)

    # Weighted sum
    if duration_ms:
        raw = title_score * 0.50 + artist_score * 0.25 + duration_score * 0.25
    else:
        raw = title_score * 0.65 + artist_score * 0.35

    # 4. Bad-keyword penalty
    title_lower = yt_title.lower()
    penalties = sum(1 for kw in BAD_KEYWORDS if kw in title_lower)
    raw = max(0.0, raw - 0.30 * penalties)

    return round(raw, 4)


def _build_search_queries(artist: str, track: str) -> list[str]:
    """
    Return progressively broader search queries to try in order.

    Most specific first (best chance of correct video), broadening
    on each fallback attempt.
    """
    return [
        f"{artist} - {track} official audio",
        f"{artist} {track} official audio",
        f"{artist} - {track} audio",
        f"{artist} {track}",
    ]


def download_from_youtube(
    artist: str,
    track: str,
    duration_ms: Optional[int] = None
) -> Optional[str]:
    """
    Search YouTube, pick the best-matching audio, and download as MP3.

    Integrity strategy:
      1. Fetch CANDIDATE_COUNT results for several search query variants.
      2. Score every candidate with _score_candidate().
      3. Accept the highest-scoring candidate that meets MIN_INTEGRITY_SCORE.
      4. If nothing passes the threshold, log and return None.

    Args:
        artist:      Artist name from CSV.
        track:       Track name from CSV.
        duration_ms: Track duration in milliseconds from CSV (improves accuracy).

    Returns:
        Path to downloaded MP3 file, or None if no acceptable match was found.
    """
    filename = f"{sanitize_filename(artist)} - {sanitize_filename(track)}"
    output_path = str(Path(DOWNLOADS_FOLDER) / filename)

    queries = _build_search_queries(artist, track)
    best_entry = None
    best_score = -1.0
    best_query_label = ''

    # --- Phase 1: Collect and score candidates across all query variants ---
    fetch_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'extract_flat': False,  # We need full info (duration etc.)
        'skip_download': True,
    }

    for query in queries:
        search_query = f"ytsearch{CANDIDATE_COUNT}:{query}"
        try:
            with yt_dlp.YoutubeDL(fetch_opts) as ydl:
                info = ydl.extract_info(search_query, download=False)

            if not info or 'entries' not in info:
                continue

            for entry in (info['entries'] or []):
                if not entry:
                    continue
                score = _score_candidate(entry, artist, track, duration_ms)
                if score > best_score:
                    best_score = score
                    best_entry = entry
                    best_query_label = query

        except Exception as e:
            print(f"  ⚠️  Search error for '{query}': {e}")
            continue

    # --- Phase 2: Integrity gate ---
    if best_entry is None or best_score < MIN_INTEGRITY_SCORE:
        reason = (
            f"best score {best_score:.2f} below threshold {MIN_INTEGRITY_SCORE}"
            if best_entry else "no results found"
        )
        log_failure(artist, track, f"Integrity check failed – {reason}")
        print(
            f"  ❌ Integrity FAIL for '{artist} - {track}' "
            f"(score={best_score:.2f})"
        )
        return None

    yt_title = best_entry.get('title', 'Unknown')
    yt_url = best_entry.get('webpage_url', '')
    print(
        f"  ✅ Integrity OK  score={best_score:.2f}  "
        f"query='{best_query_label}'\n"
        f"     YT title : {yt_title}\n"
        f"     YT url   : {yt_url}"
    )

    # --- Phase 3: Download the chosen candidate ---
    download_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': AUDIO_QUALITY,
        }],
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
    }

    try:
        with yt_dlp.YoutubeDL(download_opts) as ydl:
            ydl.download([yt_url])
    except Exception as e:
        log_failure(artist, track, f"YouTube download error: {str(e)}")
        return None

    mp3_path = f"{output_path}.mp3"
    if not Path(mp3_path).exists():
        log_failure(artist, track, "Download completed but MP3 file not found")
        return None

    return mp3_path


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
    cover_art_path: Optional[str] = None,
    isrc: Optional[str] = None,
    track_number: Optional[str] = None,
    disc_number: Optional[str] = None,
) -> bool:
    """
    Embed ID3 tags and cover art into MP3 file.

    Embeds all available Spotify metadata as ID3 tags:
      TIT2  – Track title
      TPE1  – Artist(s)
      TALB  – Album name
      APIC  – Front cover art
      TSRC  – ISRC (unique recording identifier from Spotify)
      TRCK  – Track number
      TPOS  – Disc number

    Args:
        mp3_path:      Path to MP3 file.
        title:         Track title.
        artist:        Full artist string (comma-separated for multi-artist).
        album:         Album name.
        cover_art_path: Optional path to cover art image.
        isrc:          ISRC code from Spotify CSV.
        track_number:  Track number (e.g. '4' or '4/12').
        disc_number:   Disc number (e.g. '1').

    Returns:
        True if successful, False otherwise.
    """
    try:
        # Load or create ID3 tags
        try:
            audio = MP3(mp3_path, ID3=ID3)
            audio.add_tags()
        except Exception:
            audio = MP3(mp3_path)

        # Core text tags
        audio.tags.add(TIT2(encoding=3, text=title))
        audio.tags.add(TPE1(encoding=3, text=artist))
        audio.tags.add(TALB(encoding=3, text=album))

        # Optional enriched tags
        if isrc:
            audio.tags.add(TSRC(encoding=3, text=isrc))
        if track_number:
            audio.tags.add(TRCK(encoding=3, text=str(track_number)))
        if disc_number:
            audio.tags.add(TPOS(encoding=3, text=str(disc_number)))

        # Embed cover art (APIC frame)
        if cover_art_path and Path(cover_art_path).exists():
            try:
                with open(cover_art_path, "rb") as img_file:
                    audio.tags.add(
                        APIC(
                            encoding=3,
                            mime='image/jpeg',
                            type=3,        # Cover (front)
                            desc='Cover',
                            data=img_file.read()
                        )
                    )
            except Exception:
                pass

        audio.save()
        return True

    except Exception:
        return False


# ============================================================================
# Main Processing Loop
# ============================================================================

def _safe_col(row: pd.Series, col: str, default: str = '') -> str:
    """Safely read a column from a row, returning default if missing or NaN."""
    if col not in row.index:
        return default
    val = row[col]
    if pd.isna(val):
        return default
    return str(val).strip()


def _primary_artist(artist_str: str) -> str:
    """
    Extract the primary (first listed) artist from a potentially
    comma-separated multi-artist string.

    E.g. 'superdupersultan, JANI' → 'superdupersultan'
    """
    return artist_str.split(',')[0].strip()


def process_playlist(csv_path: str) -> dict:
    """
    Main processing loop: reads CSV and downloads songs with metadata.

    Handles the full Spotify CSV schema:
      - Track Duration (ms) → tighter integrity matching
      - ISRC               → embedded as TSRC ID3 tag
      - Track Number       → embedded as TRCK ID3 tag
      - Disc Number        → embedded as TPOS ID3 tag
      - Multi-artist       → all artists embedded; primary used for search

    Args:
        csv_path: Path to playlist CSV file

    Returns:
        Dictionary with statistics (processed, skipped, failed)
    """
    df = validate_and_fix_csv(csv_path)
    stats = {'processed': 0, 'skipped': 0, 'failed': 0}

    with tqdm(total=len(df), desc="Processing songs", unit="song") as pbar:
        for _, row in df.iterrows():
            track    = _safe_col(row, 'Track Name')
            artist   = _safe_col(row, 'Artist Name')       # may be multi-artist
            album    = _safe_col(row, 'Album Name')
            image_url = _safe_col(row, 'Album Image URL')

            # Enriched Spotify fields
            isrc         = _safe_col(row, 'ISRC') or None
            track_number = _safe_col(row, 'Track Number') or None
            disc_number  = _safe_col(row, 'Disc Number') or None

            # Duration for integrity scorer
            duration_ms: Optional[int] = None
            raw_dur = _safe_col(row, 'Track Duration (ms)')
            if raw_dur:
                try:
                    duration_ms = int(float(raw_dur))
                except (ValueError, TypeError):
                    pass

            # For search and file naming, use the primary (first) artist
            search_artist = _primary_artist(artist)

            if isrc:
                pbar.set_description(f"Processing: {search_artist} - {track} [{isrc}]")
            else:
                pbar.set_description(f"Processing: {search_artist} - {track}")

            # Smart Skip: file already exists?
            if file_exists(search_artist, track):
                print(f"✓ Already exists: {search_artist} - {track}")
                stats['skipped'] += 1
                pbar.update(1)
                continue

            # Download from YouTube with integrity check
            mp3_path = download_from_youtube(search_artist, track, duration_ms)
            if not mp3_path:
                stats['failed'] += 1
                pbar.update(1)
                continue

            # Download cover art
            cover_art_path = download_cover_art(image_url)

            # Embed all metadata (full artist string preserved in tags)
            success = embed_metadata(
                mp3_path, track, artist, album,
                cover_art_path=cover_art_path,
                isrc=isrc,
                track_number=track_number,
                disc_number=disc_number,
            )

            if cover_art_path and Path(cover_art_path).exists():
                try:
                    Path(cover_art_path).unlink()
                except Exception:
                    pass

            if success:
                stats['processed'] += 1
            else:
                log_failure(search_artist, track, "Metadata embedding failed")
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
