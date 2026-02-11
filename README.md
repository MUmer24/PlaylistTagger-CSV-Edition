# PlaylistTagger - CSV Edition

> Build personal music libraries from CSV playlists with rich metadata

A Python CLI application that helps you create properly-tagged local music collections from playlist exports. Reads playlist data from CSV, retrieves audio sources, and embeds complete metadata including cover art—perfect for archiving personal music libraries.

---

## Features

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

1. **Clone or download this project**

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

Your CSV must have these headers:
- `Track Name`
- `Artist Name`
- `Album Name`
- `Album Image URL`

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

## Contributing

This project is provided as-is for educational and personal use.

---

## Contributing

This is a complete, self-contained project. Feel free to fork and modify for your needs!

---

## Credits

Built with:
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [mutagen](https://mutagen.readthedocs.io/) - Audio metadata library
- [pandas](https://pandas.pydata.org/) - Data processing

---

**Happy Music Downloading! 🎵**
