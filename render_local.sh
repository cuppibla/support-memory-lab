#!/bin/bash
# Render CODELAB.md locally. The committed file references public GCS image
# URLs; local claat segfaults fetching remote images, so: swap IMAGE EMBEDS
# (only) to local copies, render, then rewrite the HTML back to GCS URLs.
# Plain links to GCS (e.g. the photo download link) are never touched.
set -e
cd "$(dirname "$0")"
python3 - << 'PY'
import re
s = open("CODELAB.md").read()
s = re.sub(r'(!\[[^\]]*\]\()https://storage\.googleapis\.com/support-memory-lab-assets/img/',
           r'\1codelab-assets/', s)
open(".codelab_local.md", "w").write(s)
PY
~/go/bin/claat export -o . .codelab_local.md
rm .codelab_local.md
python3 - << 'PY'
import hashlib, pathlib, re
out = pathlib.Path("agent-memory-layer-by-layer")
assets = {hashlib.md5(p.read_bytes()).hexdigest(): p.name
          for p in pathlib.Path("codelab-assets").iterdir() if p.is_file()}
html = (out / "index.html").read_text()
swapped = 0
for img in (out / "img").iterdir():
    h = hashlib.md5(img.read_bytes()).hexdigest()
    if h in assets:
        url = "https://storage.googleapis.com/support-memory-lab-assets/img/" + assets[h]
        html, n = re.subn(re.escape(f"img/{img.name}"), url, html)
        swapped += n
        img.unlink()
(out / "index.html").write_text(html)
print(f"rewrote {swapped} image refs to GCS; local img/ copies removed")
PY
