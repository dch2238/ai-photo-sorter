"""Generate a self-contained offline HTML album viewer (`album.html`) inside the sorted media folder.
Features:
- Instant 1-click Delete directly to macOS/Windows Trash (zero 'marked for deletion' clutter).
- Video player, Lightbox zoom, 60 FPS lazy grid, relative paths for 100% portability.
"""
import glob, json, os, re, shutil, sys

sys.path.insert(0, os.path.dirname(__file__))
from common import CATEGORIES, DATA, LABELS, categories, load

def generate_album(dest_dir):
    dest_dir = os.path.abspath(os.path.expanduser(dest_dir))
    if not os.path.exists(dest_dir):
        sys.exit(f"Destination folder does not exist: {dest_dir}")

    print(f"Generating offline HTML album in: {dest_dir}")
    inv = load(os.path.join(DATA, "inventory.json"), [])
    cats = categories()
    cat_map = {c["key"]: c for c in cats}
    
    # Load all labels
    labels = {}
    for f in sorted(glob.glob(os.path.join(LABELS, "*.json"))):
        labels.update(load(f, {}))
        
    thumbs_src = os.path.join(DATA, "thumbs")
    thumbs_dest = os.path.join(dest_dir, ".thumbnails")
    os.makedirs(thumbs_dest, exist_ok=True)
    
    # Check for people clusters

    # Build item manifest with relative paths
    items = []
    for r in inv:
        cat_key = labels.get(str(r["id"]), "other")
        cat_info = cat_map.get(cat_key, {"label": "Other", "emoji": "📁", "kind": r.get("kind", "photo")})
        folder_name = cat_info["label"].replace("&", "and")
        
        rel_media_path = f"{folder_name}/{r['name']}"
        full_media_path = os.path.join(dest_dir, folder_name, r["name"])
        exists_in_sorted = os.path.exists(full_media_path)
        
        items.append({
            "id": r["id"],
            "name": r["name"],
            "ext": r.get("ext", "").lower(),
            "kind": r.get("kind", "photo"),
            "bytes": r.get("bytes", 0),
            "w": r.get("w", 0),
            "h": r.get("h", 0),
            "cat": cat_key,
            "cat_label": cat_info["label"],
            "cat_emoji": cat_info.get("emoji", "📁"),
            "folder": folder_name,
            "rel_path": rel_media_path if exists_in_sorted else r["path"],
            "is_sorted": exists_in_sorted,
            "thumb": f".thumbnails/{r['id']}.jpg"
        })

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Offline Media Album</title>
<style>
:root {{
  --bg: #0d1117;
  --surface: #161b22;
  --surface-hover: #21262d;
  --border: #30363d;
  --text: #c9d1d9;
  --text-bright: #f0f6fc;
  --text-muted: #8b949e;
  --primary: #58a6ff;
  --danger: #f85149;
  --danger-bg: rgba(248, 81, 73, 0.15);
  --success: #3fb950;
  --warning: #d29922;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
body {{ background: var(--bg); color: var(--text); display: flex; height: 100vh; overflow: hidden; }}

/* Sidebar */
aside {{
  width: 270px; min-width: 270px; background: var(--surface); border-right: 1px solid var(--border);
  display: flex; flex-direction: column; height: 100vh;
}}
.sidebar-header {{
  padding: 16px; border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between;
}}
.sidebar-header h1 {{ font-size: 1.1rem; color: var(--text-bright); font-weight: 600; display: flex; align-items: center; gap: 8px; }}
.category-list {{ flex: 1; overflow-y: auto; padding: 12px 8px; list-style: none; }}
.cat-item {{
  display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; border-radius: 6px;
  cursor: pointer; margin-bottom: 2px; font-size: 0.9rem; transition: background 0.15s;
}}
.cat-item:hover {{ background: var(--surface-hover); }}
.cat-item.active {{ background: #1f6feb33; color: var(--primary); font-weight: 600; }}
.cat-left {{ display: flex; align-items: center; gap: 10px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.cat-count {{ font-size: 0.75rem; background: var(--border); padding: 2px 7px; border-radius: 10px; color: var(--text-muted); }}
.cat-item.active .cat-count {{ background: var(--primary); color: #000; font-weight: 700; }}

/* Main Area */
main {{ flex: 1; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }}
.topbar {{
  height: 60px; min-height: 60px; border-bottom: 1px solid var(--border); display: flex; align-items: center;
  justify-content: space-between; padding: 0 20px; background: var(--surface); gap: 16px;
}}
.top-title {{ font-size: 1.1rem; font-weight: 600; color: var(--text-bright); display: flex; align-items: center; gap: 10px; }}
.top-actions {{ display: flex; align-items: center; gap: 12px; }}
.search-input {{
  background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 6px 12px;
  color: var(--text); font-size: 0.85rem; outline: none; width: 220px;
}}
.search-input:focus {{ border-color: var(--primary); }}
.filter-pill {{
  background: var(--bg); border: 1px solid var(--border); padding: 6px 12px; border-radius: 20px;
  font-size: 0.8rem; cursor: pointer; color: var(--text-muted); transition: all 0.15s;
}}
.filter-pill:hover {{ color: var(--text); }}
.filter-pill.active {{ background: var(--primary); color: #000; font-weight: 600; border-color: var(--primary); }}

function init() {{
  buildSidebar();
  renderGrid();
}}

function buildSidebar() {{
  const list = document.getElementById('catList');
  list.innerHTML = '';
  
  // All Media item
  const allLi = document.createElement('li');
  allLi.className = 'cat-item' + (currentCategory === 'all' ? ' active' : '');
  allLi.onclick = () => selectCategory('all');
  allLi.innerHTML = `
    <div class="cat-left"><span>🌟</span><span>All Media</span></div>
    <span class="cat-count">${{ITEMS.filter(it => !deletedIds.has(it.id)).length}}</span>
  `;
  list.appendChild(allLi);

  // Group counts
  const counts = {{}};
  ITEMS.forEach(it => {{
    if (!deletedIds.has(it.id)) {{
      counts[it.cat] = (counts[it.cat] || 0) + 1;
    }}
  }});

  CATS.forEach(c => {{
    const cnt = counts[c.key] || 0;
    if (cnt === 0) return;
    const li = document.createElement('li');
    li.className = 'cat-item' + (currentCategory === c.key ? ' active' : '');
    li.onclick = () => selectCategory(c.key);
    li.innerHTML = `
      <div class="cat-left"><span>${{c.emoji}}</span><span>${{c.label}}</span></div>
      <span class="cat-count">${{cnt}}</span>
    `;
    list.appendChild(li);
  }});
}}

function selectCategory(catKey) {{
  currentCategory = catKey;
  selectedPersonId = null;
  buildSidebar();

  const cat = CATS.find(c => c.key === catKey);
  document.getElementById('currentTitle').innerHTML = cat 
    ? `<span>${{cat.emoji}}</span> ${{cat.label}}`
    : `<span>🌟</span> All Media`;
  renderGrid();
}}

function filterByPerson(personId) {{
  selectedPersonId = (selectedPersonId === personId) ? null : personId;
  const person = CLUSTERS.find(c => c.id === selectedPersonId);
  if (person) {{
    document.getElementById('currentTitle').innerHTML = `<span>👤</span> ${{person.name}} (${{person.count}} photos)`;
  }} else {{
    const cat = CATS.find(c => c.key === currentCategory);
    document.getElementById('currentTitle').innerHTML = cat 
      ? `<span>${{cat.emoji}}</span> ${{cat.label}}`
      : `<span>🌟</span> All Media`;
  }}
  renderGrid();
}}

function setFilter(type) {{
  currentFilter = type;
  document.getElementById('filterAll').className = 'filter-pill' + (type === 'all' ? ' active' : '');
  document.getElementById('filterPhotos').className = 'filter-pill' + (type === 'photo' ? ' active' : '');
  document.getElementById('filterVideos').className = 'filter-pill' + (type === 'video' ? ' active' : '');
  renderGrid();
}}

function handleSearch() {{
  searchQuery = document.getElementById('searchInput').value.trim().toLowerCase();
  renderGrid();
}}

function renderGrid() {{
  const grid = document.getElementById('galleryGrid');
  grid.innerHTML = '';

  const personCluster = selectedPersonId ? CLUSTERS.find(c => c.id === selectedPersonId) : null;
  const personItemIds = personCluster ? new Set(personCluster.item_ids) : null;

  visibleItems = ITEMS.filter(it => {{
    if (deletedIds.has(it.id)) return false;
    if (personItemIds && !personItemIds.has(it.id)) return false;
    if (!personItemIds && currentCategory !== 'all' && it.cat !== currentCategory) return false;
    if (currentFilter !== 'all' && it.kind !== currentFilter) return false;
    if (searchQuery && !it.name.toLowerCase().includes(searchQuery)) return false;
    return true;
  }});

  visibleItems.forEach((it, idx) => {{
    const card = document.createElement('div');
    card.id = `card-${{it.id}}`;
    card.className = 'card';
    card.onclick = () => openLightbox(idx);

    const isVid = it.kind === 'video';
    card.innerHTML = `
      <img src="${{it.thumb}}" loading="lazy" alt="${{it.name}}">
      <button class="card-del-btn" title="Delete immediately" onclick="event.stopPropagation(); executeDelete(${{it.id}})">🗑️</button>
      ${{isVid ? '<span class="video-pill">▶ VIDEO</span>' : ''}}
      <span class="card-badge">${{it.name}}</span>
    `;
    grid.appendChild(card);
  }});
}}

async function executeDelete(id) {{
  const card = document.getElementById(`card-${{id}}`);
  if (card) card.classList.add('deleting');

  deletedIds.add(id);
  localStorage.setItem('album_deleted_ids', JSON.stringify([...deletedIds]));
  
  // Call server delete API
  try {{
    const res = await fetch('http://127.0.0.1:8765/api/delete', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ id: id, delete_original: false }})
    }});
    if (res.ok) {{
      showToast("🗑️ Moved file to Mac Trash!");
    }}
  }} catch (e) {{
    console.log("Delete called offline");
  }}

  setTimeout(() => {{
    buildSidebar();
    renderGrid();
  }}, 200);
}}

function showToast(msg) {{
  let toast = document.getElementById('albumToast');
  if (!toast) {{
    toast = document.createElement('div');
    toast.id = 'albumToast';
    toast.style.cssText = 'position:fixed;bottom:24px;right:24px;background:#238636;color:#fff;padding:12px 20px;border-radius:8px;font-size:0.9rem;font-weight:600;z-index:9999;box-shadow:0 8px 24px rgba(0,0,0,0.5);transition:opacity 0.2s;';
    document.body.appendChild(toast);
  }}
  toast.innerText = msg;
  toast.style.opacity = '1';
  clearTimeout(window._toastTimer);
  window._toastTimer = setTimeout(() => {{ toast.style.opacity = '0'; }}, 2500);
}}

function openLightbox(index) {{
  currentLbIndex = index;
  const it = visibleItems[index];
  if (!it) return;

  const lb = document.getElementById('lightbox');
  const content = document.getElementById('lbContent');
  const info = document.getElementById('lbInfo');
  
  const sizeMB = (it.bytes / (1024 * 1024)).toFixed(1);
  info.innerHTML = `<strong>${{it.name}}</strong> &bull; ${{it.folder}} &bull; ${{sizeMB}} MB (${{index + 1}} of ${{visibleItems.length}})`;

  if (it.kind === 'video') {{
    content.innerHTML = `<video src="${{encodeURI(it.rel_path)}}" controls autoplay playsinline style="max-height:80vh; max-width:90vw;"></video>`;
  }} else {{
    content.innerHTML = `<img src="${{encodeURI(it.rel_path)}}" style="max-height:80vh; max-width:90vw;">`;
  }}

  lb.classList.add('open');
}}

function closeLightbox() {{
  const lb = document.getElementById('lightbox');
  lb.classList.remove('open');
  document.getElementById('lbContent').innerHTML = '';
}}

function prevLightbox() {{
  if (currentLbIndex > 0) openLightbox(currentLbIndex - 1);
}}

function nextLightbox() {{
  if (currentLbIndex < visibleItems.length - 1) openLightbox(currentLbIndex + 1);
}}

function deleteCurrentLightboxItem() {{
  const it = visibleItems[currentLbIndex];
  if (!it) return;
  executeDelete(it.id);
  if (currentLbIndex < visibleItems.length - 1) {{
    openLightbox(currentLbIndex);
  }} else if (visibleItems.length > 0) {{
    openLightbox(Math.max(0, visibleItems.length - 1));
  }} else {{
    closeLightbox();
  }}
}}

window.addEventListener('keydown', (e) => {{
  const lbOpen = document.getElementById('lightbox').classList.contains('open');
  if (!lbOpen) return;
  if (e.key === 'Escape') closeLightbox();
  else if (e.key === 'ArrowLeft') prevLightbox();
  else if (e.key === 'ArrowRight') nextLightbox();
  else if (e.key === 'Delete' || e.key === 'Backspace') deleteCurrentLightboxItem();
}});

init();
</script>
</body>
</html>
"""

    album_file = os.path.join(dest_dir, "album.html")
    with open(album_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Successfully generated standalone album: {album_file}")
    return album_file

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "/Volumes/Extreme Pro/nov bk (sorted)"
    generate_album(target)
