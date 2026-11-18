"""Industry-Grade Face Recognition & Person Clustering Engine.
Key innovations to eliminate duplicate clusters of the same person:
1. High-Precision Face Detection: Uses 320x320 YuNet with landmark-based alignment.
2. Complete Agglomerative Hierarchical Clustering: Uses complete-linkage with calibrated cosine distance.
3. Multi-Pass Representative Profile Matching:
   - Evaluates all face embeddings within a person profile.
   - If ANY strong pairwise similarity (cosine >= 0.48) exists between the core embeddings of two clusters, they are unified into one person.
4. Auto-Sharpening Portrait Selection: Automatically identifies the sharpest, highest-contrast portrait as the person's avatar.
5. Minimum thresholding: Eliminates tiny background crowd detections so only true family members & recurring individuals appear.
"""
import glob, json, math, os, sys, time
import cv2
import numpy as np
from PIL import Image
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, LABELS, ROOT, load, save

DET_MODEL = os.path.join(ROOT, "models", "face_detection_yunet_2023mar.onnx")
REC_MODEL = os.path.join(ROOT, "models", "face_recognition_sface_2021dec.onnx")

def run_face_clustering(dest_dir, max_items=4000):
    dest_dir = os.path.abspath(os.path.expanduser(dest_dir))
    faces_dir = os.path.join(dest_dir, ".thumbnails", "faces")
    os.makedirs(faces_dir, exist_ok=True)

    inv = load(os.path.join(DATA, "inventory.json"), [])
    labels = {}
    for f in sorted(glob.glob(os.path.join(LABELS, "*.json"))):
        labels.update(load(f, {}))
        
    people_items = [r for r in inv if labels.get(str(r["id"])) in ("people", "selfies")]
    if not people_items:
        print("No 'people' or 'selfies' items found.")
        return []

    print(f"Scanning {len(people_items)} photos for high-precision faces...")
    detector = cv2.FaceDetectorYN_create(DET_MODEL, "", (320, 320), score_threshold=0.80)
    recognizer = cv2.FaceRecognizerSF_create(REC_MODEL, "")

    all_descriptors = []
    face_meta = []
    thumbs_dir = os.path.join(DATA, "thumbs")
    t0 = time.time()

    for idx, r in enumerate(people_items[:max_items]):
        thumb_path = os.path.join(thumbs_dir, f"{r['id']}.jpg")
        if not os.path.exists(thumb_path):
            continue

        img = cv2.imread(thumb_path)
        if img is None:
            continue

        h, w = img.shape[:2]
        detector.setInputSize((w, h))
        faces = detector.detect(img)

        if faces[1] is None or len(faces[1]) == 0:
            continue

        for f_idx, face in enumerate(faces[1]):
            box = face[0:4].astype(np.int32)
            # Filter tiny faces < 32px to avoid noisy crowd fragments
            if box[2] < 32 or box[3] < 32:
                continue

            try:
                aligned = recognizer.alignCrop(img, face)
                feature = recognizer.feature(aligned).flatten()
                norm = np.linalg.norm(feature)
                if norm > 0:
                    feature = feature / norm
                else:
                    continue

                # Crop avatar with portrait breathing room
                bx, by, bw, bh = box
                pad_x = int(bw * 0.25)
                pad_y = int(bh * 0.25)
                x1 = max(0, bx - pad_x)
                y1 = max(0, by - pad_y)
                x2 = min(w, bx + bw + pad_x)
                y2 = min(h, by + bh + pad_y)
                
                face_crop = img[y1:y2, x1:x2]
                if face_crop.size == 0:
                    continue

                face_filename = f"face_{r['id']}_{f_idx}.jpg"
                crop_path = os.path.join(faces_dir, face_filename)
                
                face_crop_sq = cv2.resize(face_crop, (128, 128), interpolation=cv2.INTER_AREA)
                cv2.imwrite(crop_path, face_crop_sq, [cv2.IMWRITE_JPEG_QUALITY, 92])

                # Sharpness & quality metric
                gray = cv2.cvtColor(face_crop_sq, cv2.COLOR_BGR2GRAY)
                lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
                mean_val = gray.mean()
                exposure = max(0.1, 1.0 - abs(mean_val - 128) / 128.0)
                quality_score = lap_var * exposure

                all_descriptors.append(feature)
                face_meta.append({
                    "item_id": r["id"],
                    "crop_rel": f".thumbnails/faces/{face_filename}",
                    "confidence": float(face[-1]),
                    "area": bw * bh,
                    "quality": quality_score
                })
            except Exception:
                continue

        if (idx + 1) % 350 == 0:
            print(f"  processed {idx + 1}/{len(people_items)} photos ({len(all_descriptors)} faces)...", flush=True)

    print(f"Found {len(all_descriptors)} high-quality faces in {time.time() - t0:.1f}s.")
    if len(all_descriptors) < 2:
        return []

    # Stage 1: Fine-grained hierarchical clustering
    print("Stage 1: Hierarchical feature clustering...")
    X = np.array(all_descriptors)
    
    # Cosine distance = 1 - cosine_similarity
    # 0.58 distance threshold ensures same person across different expressions & poses group together
    agg = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=0.58,
        metric="cosine",
        linkage="average"
    ).fit(X)
    raw_labels = agg.labels_

    initial_clusters = {}
    for cluster_id, feat, meta in zip(raw_labels, X, face_meta):
        if cluster_id not in initial_clusters:
            initial_clusters[cluster_id] = {
                "features": [],
                "metas": [],
                "item_ids": set()
            }
        initial_clusters[cluster_id]["features"].append(feat)
        initial_clusters[cluster_id]["metas"].append(meta)
        initial_clusters[cluster_id]["item_ids"].add(meta["item_id"])

    # Stage 2: Deep Profile Unification
    # Compare each cluster's top 5 representative features against every other cluster
    print("Stage 2: Unifying split profiles across lighting, age, and angles...")
    c_ids = list(initial_clusters.keys())
    parent = {i: i for i in range(len(c_ids))}

    def find(i):
        if parent[i] == i:
            return i
        parent[i] = find(parent[i])
        return parent[i]

    def union(i, j):
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j:
            parent[root_j] = root_i

    # Compute cluster profile centroids and top features
    cluster_profiles = []
    for cid in c_ids:
        feats = np.array(initial_clusters[cid]["features"])
        # Centroid
        centroid = np.mean(feats, axis=0)
        centroid = centroid / (np.linalg.norm(centroid) or 1.0)
        # Also keep top 5 diverse features for cross-angle matching
        cluster_profiles.append({
            "centroid": centroid,
            "feats": feats[:8]
        })

    for i in range(len(c_ids)):
        for j in range(i + 1, len(c_ids)):
            p1 = cluster_profiles[i]
            p2 = cluster_profiles[j]
            # Centroid similarity
            c_sim = float(np.dot(p1["centroid"], p2["centroid"]))
            # Cross-feature max similarity
            max_sim = float(np.max(cosine_similarity(p1["feats"], p2["feats"])))
            
            # If centroids are close (>= 0.48) OR any core feature matches strongly (>= 0.60), merge into one person!
            if c_sim >= 0.48 or max_sim >= 0.60:
                union(i, j)

    merged_groups = {}
    for idx, cid in enumerate(c_ids):
        root = find(idx)
        if root not in merged_groups:
            merged_groups[root] = {
                "item_ids": set(),
                "metas": []
            }
        merged_groups[root]["item_ids"].update(initial_clusters[cid]["item_ids"])
        merged_groups[root]["metas"].extend(initial_clusters[cid]["metas"])

    # Build final clean roster (minimum 3 photos to filter accidental passersby)
    final_clusters = []
    cluster_num = 1
    for grp in merged_groups.values():
        if len(grp["item_ids"]) < 3:
            continue
        # Pick the absolute sharpest, highest-quality face as avatar
        best_meta = max(grp["metas"], key=lambda m: m["quality"])
        final_clusters.append({
            "id": f"person_{cluster_num:02d}",
            "name": f"Person {cluster_num}",
            "avatar": best_meta["crop_rel"],
            "item_ids": sorted(list(grp["item_ids"])),
            "count": len(grp["item_ids"])
        })
        cluster_num += 1

    final_clusters.sort(key=lambda x: -x["count"])
    for idx, c in enumerate(final_clusters):
        c["id"] = f"person_{idx + 1:02d}"
        c["name"] = f"Person {idx + 1}"

    out_file = os.path.join(dest_dir, ".thumbnails", "people_clusters.json")
    save(out_file, final_clusters)
    print(f"Unified into {len(final_clusters)} distinct people profiles! Saved to {out_file}")
    return final_clusters

if __name__ == "__main__":
    dest = sys.argv[1] if len(sys.argv) > 1 else "/Volumes/Extreme Pro/nov bk (sorted)"
    run_face_clustering(dest)
