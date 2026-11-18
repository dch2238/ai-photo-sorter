# AI Photo Sorter

An open-source, privacy-first desktop application that scans, deduplicates, categorizes, and organizes large camera rolls and video archives directly on your machine.

- **100% On-Device & Private**: Your original media files are never altered, moved, or deleted from their source location.
- **Multimodal AI Categorization**: Fast batch classification with Gemini Vision API (or local heuristics) into intuitive albums: *People & Family, Travel, Food & Drinks, Everyday Clips, Documents, Selfies, and more*.
- **Duplicate Detection**: Identifies byte-identical files, re-saved screenshots, and rapid burst shots into a dedicated review folder.
- **Standalone Offline Album (`album.html`)**: Generates a self-contained, 60 FPS HTML album directly inside your sorted folder. Double-click to browse and play 4K videos natively with zero background servers.
- **Instant System Trash**: Deleting an unwanted photo or video immediately moves it to your native macOS Trash or Windows Recycle Bin with full "Put Back" capability.

---

## Quick Start

### 1. Clone the Repository
```bash
git clone -b dc https://github.com/dch2238/ai-photo-sorter.git
cd ai-photo-sorter
```

### 2. Setup Dependencies
```bash
./setup.sh
```
*(Creates an isolated Python virtual environment in `.venv/` and installs required packages).*

### 3. Launch Dashboard
```bash
./start.sh
```
Or double-click `Open Photo Sorter.command` on macOS. The dashboard opens automatically at `http://127.0.0.1:8765`.

---

## Configuration & Usage

### Gemini Vision API (Recommended)
Add your Gemini API key to `.env` in the project root:
```bash
GEMINI_API_KEY="your-api-key-here"
```
The sorter will automatically use Gemini Vision batch classification to categorize photos and videos with high accuracy.

### In the Dashboard:
1. **Choose folder**: Select the folder with your photos (Google Photos export, Apple Photos unmodified originals, or camera SD card).
2. **Choose destination**: Select where your organized folder should be created.
3. Click **Start AI Sorting**.

---

## Standalone Offline Album (`album.html`)
Once sorting completes, an `album.html` file is generated inside your destination folder:
- **Zero background server needed**: Double-click anytime to open in Safari, Chrome, or Edge.
- **60 FPS Grid**: Fast smooth scrolling with embedded thumbnail previews.
- **Built-in Video Player**: Play 4K and 1080p clips directly in the lightbox.
- **Instant Trash**: Delete items directly from the album into macOS Trash.
