# PlaylistTagger - CSV Edition

> Build personal music libraries from CSV playlists with rich metadata

A Python CLI application that helps you create properly-tagged local music collections from playlist exports. Reads playlist data from CSV, retrieves audio sources, and embeds complete metadata including cover art—perfect for archiving personal music libraries.

---

## Features

✅ **Smart CSV Mapping** - Auto-detects and fixes column name variations  
✅ **CSV Playlist Support** - Works with standard Spotify export formats  
✅ **Smart Skip** - Resume interrupted downloads automatically  
✅ **Rich Metadata** - Embeds Title, Artist, Album, and Cover Art  
✅ **Error Resilient** - Continues processing even when songs fail  
✅ **Progress Tracking** - Real-time progress bar with current song  
✅ **Comprehensive Logging** - Detailed success and failure logs  

---

## Prerequisites

- **Python 3.10+**
- **FFmpeg** (required by yt-dlp for audio conversion)

### Installing FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MUmer24/PlaylistTagger-CSV-Edition.git
   cd PlaylistTagger-CSV-Edition
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### 1. Prepare Your CSV

Export your Spotify playlist using a tool like [Exportify](https://watsonbox.github.io/exportify/).

**Required Data (Flexible Column Names):**

The script automatically detects and maps common column name variations. Your CSV needs these data fields, but the exact column names are flexible:

- **Track Name** (alt: `Song Name`, `Title`, `Track`, etc.)
- **Artist Name** (alt: `Artist`, `Artist(s)`, `Artists`, etc.)
- **Album Name** (alt: `Album`, etc.)
- **Album Image URL** (alt: `Cover Art`, `Image URL`, `Cover`, etc.)

> 💡 **Smart Mapping:** The script will automatically detect and rename columns like `"Song Name"` → `"Track Name"` or `"Artist(s)"` → `"Artist Name"` when you run it.

Save the file as `playlist.csv` in the project folder.

### 2. Run the Script

```bash
python main.py
```

### 3. Output

- **Downloaded MP3s:** `downloads/` folder
- **Success Summary:** `summary_log.txt`
- **Failed Songs:** `failed_log.txt` (if any failures occur)

---

## How It Works

### The Metadata Bridge

```
CSV (Spotify Export)
  ↓
YouTube Search & Download
  ↓
Metadata Embedding
  ├─ Title (TIT2)
  ├─ Artist (TPE1)
  ├─ Album (TALB)
  └─ Cover Art (APIC frame)
  ↓
Tagged MP3 File
```

The script takes structured playlist data from your CSV and "stamps" it onto YouTube audio, creating properly tagged music files that work in any media player.

---

## Configuration

Default settings in `main.py`:

| Setting | Value | Modify |
|---------|-------|--------|
| **Audio Quality** | 192 kbps CBR | Change `AUDIO_QUALITY` |
| **Output Folder** | `downloads/` | Change `DOWNLOADS_FOLDER` |
| **CSV Filename** | `playlist.csv` | Update in `main()` |

---

## Features in Detail

### Smart CSV Mapping

The script includes intelligent CSV validation that automatically handles different export formats:

**Auto-Detection:**
- Recognizes 20+ common column name variations
- Maps variations like `"Song Name"`, `"Title"`, `"Track"` → `"Track Name"`
- Handles both exact matches and case-insensitive variations

**What You See:**
```
📋 CSV Validation & Column Mapping
==================================================
✓ CSV loaded successfully: 150 rows found

🔍 Column Mapping Results:
--------------------------------------------------
✓ 'Track Name' (already correct)
✓ 'Artist Name(s)' → 'Artist Name' (renamed)
✓ 'Album Name' (already correct)
✓ 'Album Image URL' (already correct)

✅ CSV Validation Complete!
✅ Ready to process 150 tracks
```

**Validation Checks:**
- Verifies all required columns are present
- Reports empty or invalid rows
- Shows data quality statistics before processing

### Smart Skip (Resumability)

If the script is interrupted, simply run it again. It will:
- Check which files already exist
- Skip completed downloads
- Continue with remaining songs

**Example:**
```
Run 1: Downloads 50/100 songs → Interrupted
Run 2: Skips 50 existing, downloads remaining 50
```

### Error Handling

The script **never crashes** on individual song failures:
- YouTube search returns no results → Logged and skipped
- Cover art download fails → Continues with text tags only
- Invalid CSV row → Logged and skipped

All failures are recorded in `failed_log.txt` for review.

---

## Troubleshooting

### "YouTube search returned no results"

**Cause:** Song not found on YouTube with the given artist/title combination.

**Solutions:**
- Edit the CSV to adjust the track/artist name
- Manually search YouTube to confirm availability

### "FFmpeg not found"

**Cause:** yt-dlp requires FFmpeg to convert audio.

**Solution:** Install FFmpeg (see Prerequisites section)

### "Metadata embedding failed"

**Cause:** Corrupted MP3 file or insufficient disk space.

**Solution:**
- Check available disk space
- Delete the corrupted file and re-run

### Cover art not appearing

**Cause:** 
- `Album Image URL` is empty/invalid in CSV
- Image download failed

**Result:** MP3 will have text tags (Title/Artist/Album) but no artwork. This is expected behavior - the script continues processing.

---

## Examples

### Basic Usage

```bash
# 1. Prepare your CSV
# 2. Run the script
python main.py

# Output:
# 🎵 PlaylistTagger - CSV Edition
# ==================================================
# Processing songs: 100%|███████████| 3/3 [00:45<00:00, 15.2s/song]
# ==================================================
# ✅ Processing Complete!
# ==================================================
# Processed: 3
# Skipped: 0
# Failed: 0
```

### Resuming Interrupted Download

```bash
# First run (interrupted after 2 songs)
python main.py  # Downloads 2/3

# Second run (resumes)
python main.py
# ✓ Already exists: Queen - Bohemian Rhapsody
# ✓ Already exists: Led Zeppelin - Stairway to Heaven
# Processing: Eagles - Hotel California  ← Downloads remaining song
```

---

## Technical Details

### Dependencies

| Package | Purpose |
|---------|---------|
| `pandas` | Robust CSV parsing |
| `yt-dlp` | YouTube search and download |
| `mutagen` | ID3 tag and cover art embedding |
| `requests` | HTTP requests for cover art |
| `tqdm` | Terminal progress bar |

### Audio Quality

- **Format:** MP3
- **Bitrate:** 192 kbps CBR (Constant Bit Rate)
- **Source:** Best available audio from YouTube

### Metadata Format

Uses ID3v2.3 tags:
- **TIT2:** Title
- **TPE1:** Artist
- **TALB:** Album
- **APIC:** Attached Picture (Cover Art)

---

## Project Structure

```
PlaylistTagger/
├── main.py              # Main application
├── requirements.txt     # Dependencies
├── playlist.csv        # Your playlist data
├── downloads/          # Output folder (auto-created)
├── failed_log.txt     # Failed songs log (created on errors)
├── summary_log.txt    # Processing summary (created after run)
└── README.md          # This file
```

---

## Legal Notice

**⚠️ IMPORTANT: For Personal Use Only**

PlaylistTagger is designed for personal, non-commercial use to build and organize your private music library. Users are responsible for:

- Ensuring they have the right to access and store the audio content
- Respecting copyright laws in their jurisdiction
- Using the tool only for personal archival purposes
- Not distributing downloaded content

This tool is provided for educational purposes and personal music library management.

---

## Contributing & Support

This is a complete, self-contained project provided for educational and personal use.

**Found a bug or have a suggestion?**
- Fork this repository and submit a pull request
- Open an issue for discussion

**For questions or help:**
- Check the Troubleshooting section above
- Review existing issues on GitHub

---

## Credits & Technologies

**Built with:**
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader and extractor
- [mutagen](https://mutagen.readthedocs.io/) - Audio metadata library for Python
- [pandas](https://pandas.pydata.org/) - Data processing and CSV handling
- [requests](https://requests.readthedocs.io/) - HTTP library for cover art downloads
- [tqdm](https://tqdm.github.io/) - Progress bar functionality

**Special Thanks:**
- [Exportify](https://watsonbox.github.io/exportify/) - Spotify playlist export tool
- [FFmpeg](https://ffmpeg.org/) - Multimedia framework for audio conversion

---

## License

This project is open source and available under the [MIT License](LICENSE).

You are free to:
- Use this software for personal or commercial purposes
- Modify and distribute the code
- Include it in your own projects

**However:** Users are responsible for ensuring their use complies with applicable copyright laws and terms of service for content sources.

---

**Happy Music Downloading! 🎵**
