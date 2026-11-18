# AI Photo Sorter

An open-source, privacy-first desktop application that scans, deduplicates, categorizes, and organizes large camera rolls and video archives directly on your machine.

- **100% On-Device & Private**: Your original media files are never altered, moved, or deleted from their source location.
- **Multimodal AI Categorization**: Fast batch classification with Gemini Vision API (or local heuristics) into intuitive albums: *People & Family, Travel, Food & Drinks, Everyday Clips, Documents, Selfies, and more*.
- **Industry-Grade Face Recognition & Clustering**: High-precision, on-device facial detection and multi-stage profile clustering (YuNet + SFace 128-dim embeddings). Groups recurring people, family members, and friends without duplicate profiles or cloud uploads.
- **Dedicated Person Galleries & Explorer**: Filter by person across your library. View all photos of an individual with quick-trash deletion.
- **Duplicate Detection**: Identifies byte-identical files, re-saved screenshots, and rapid burst shots into a dedicated review folder.
- **Standalone Offline Album (`album.html`)**: Generates a self-contained, 60 FPS HTML album directly inside your sorted folder. Double-click to browse, filter by person, and play 4K videos natively with zero background servers.
- **Instant System Trash**: Deleting an unwanted photo or video immediately moves it to your native macOS Trash or Windows Recycle Bin with full "Put Back" capability.

---

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/dch2238/ai-photo-sorter.git
cd ai-photo-sorter
```

### 2. Setup Dependencies & Face Models
```bash
./setup.sh
```
*(Creates an isolated Python virtual environment in `.venv/`, installs dependencies, and downloads lightweight, local face recognition models).*

### 3. Launch Dashboard
```bash
./start.sh
```
Or double-click `Open Photo Sorter.command` on macOS. The dashboard opens automatically at `http://127.0.0.1:8765`.

---

## Features

### 👤 Face Recognition & People Explorer
- **On-Device Neural Vision**: Employs OpenCV YuNet for face detection and SFace for 128-dimensional biometric embeddings.
- **Multi-Stage Profile Unification**: Eliminates fragmented duplicates of the same person across varied lighting, angles, expressions, and hairstyles.
- **Header Explorer ("People & Faces")**: Browse all detected individuals with sharp portrait avatars and photo counts.
- **Person Popup**: Clicking any person opens a dedicated photo gallery with instant 1-click delete to macOS Trash.
- **Folder Face Bar**: When viewing "People & family", an avatar strip lets you filter instantly by individual.

### 🤖 Multimodal AI Categorization
Add your Gemini API key to `.env` in the project root:
```bash
GEMINI_API_KEY="your-api-key-here"
```
The sorter will use Gemini Vision batch classification to categorize photos and videos with high semantic accuracy.

### 🗑️ Instant System Trash
- Click `🗑️` on any thumbnail or press `Delete`/`Backspace` in the full-screen lightbox.
- Photos are immediately moved to your native macOS Trash (`~/.Trash`) or Windows Recycle Bin—never permanently destroyed without your confirmation.

### 🌐 Standalone Offline Album (`album.html`)
Once sorting completes, an `album.html` file is generated inside your destination folder:
- **Zero background server needed**: Double-click anytime to open in Safari, Chrome, or Edge.
- **Integrated People Explorer**: Interactive face avatars right at the top of the album to filter by person offline.
- **60 FPS Grid**: Fast smooth scrolling with embedded thumbnail previews.
- **Built-in Video Player**: Play 4K and 1080p clips directly in the lightbox.

---

## License

MIT
