#!/usr/bin/env python3
"""Build the Case In Paint static site.

    python3 build.py                  # production build  -> dist/
    python3 build.py --staging        # staging build     -> dist-staging/ (served from /staging/, noindex)
    python3 build.py --staging --zip  # ...and zip it for upload to Bluehost

Content lives in content/*.json, page templates in templates/, photos in src/img/.
Requires Python 3.9+, Pillow and Jinja2 (pip install -r requirements.txt).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import zipfile
from datetime import date
from pathlib import Path

try:
    from PIL import Image, ImageOps
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    from markupsafe import Markup, escape
except ImportError:  # pragma: no cover
    sys.exit("Missing dependencies. Run: pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parent
SRC_IMG = ROOT / "src" / "img"
SRC_VIDEO = ROOT / "src" / "video"
CACHE = ROOT / ".cache" / "img"
WIDTHS = (480, 960, 1400)
OG_SIZE = (1200, 630)
BG = (11, 6, 24)  # page background, used when flattening transparent images


# ---------------------------------------------------------------- images
class Images:
    """Makes responsive WebP sizes of every master in src/img, cached between builds."""

    def __init__(self, out: Path, base: str):
        self.out = out / "img"
        self.base = base
        self.meta: dict[str, dict] = {}
        self.out.mkdir(parents=True, exist_ok=True)
        CACHE.mkdir(parents=True, exist_ok=True)

    def process_all(self):
        masters = sorted(p for p in SRC_IMG.iterdir() if p.suffix.lower() in {".webp", ".png", ".jpg", ".jpeg"})
        for p in masters:
            self._process(p)
        print(f"  images: {len(masters)} masters")

    def _process(self, path: Path):
        stem = path.stem
        digest = hashlib.md5(path.read_bytes()).hexdigest()[:10]
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im)
            w, h = im.size
            alpha = im.mode in ("RGBA", "LA", "P")
            sizes = [x for x in WIDTHS if x < w] + [min(w, WIDTHS[-1])]
            sizes = sorted(set(sizes))
            files = {}
            for sw in sizes:
                name = f"{stem}-{sw}.webp"
                cached = CACHE / f"{digest}-{name}"
                if not cached.exists():
                    copy = im.convert("RGBA" if alpha else "RGB")
                    copy.thumbnail((sw, 10_000), Image.LANCZOS)
                    copy.save(cached, "WEBP", quality=78, method=6)
                shutil.copy2(cached, self.out / name)
                files[sw] = name
        self.meta[stem] = {"w": w, "h": h, "files": files, "alpha": alpha, "digest": digest}

    def og(self, stem: str) -> str:
        """1200x630 JPEG for social cards (flattened onto the site background)."""
        m = self.meta[stem]
        name = f"og-{stem}.jpg"
        cached = CACHE / f"{m['digest']}-{name}"
        if not cached.exists():
            with Image.open(SRC_IMG / next(p.name for p in SRC_IMG.iterdir() if p.stem == stem)) as im:
                im = im.convert("RGBA")
                canvas = Image.new("RGB", OG_SIZE, BG)
                if m["alpha"]:
                    im.thumbnail((OG_SIZE[0] - 80, OG_SIZE[1] - 60), Image.LANCZOS)
                    canvas.paste(im, ((OG_SIZE[0] - im.width) // 2, (OG_SIZE[1] - im.height) // 2), im)
                else:
                    fitted = ImageOps.fit(im.convert("RGB"), OG_SIZE, Image.LANCZOS, centering=(0.5, 0.4))
                    canvas.paste(fitted)
                canvas.save(cached, "JPEG", quality=84, optimize=True, progressive=True)
        shutil.copy2(cached, self.out / name)
        return name

    # -- template helpers
    def src(self, stem: str, width: int = 1400) -> str:
        files = self.meta[stem]["files"]
        best = min(files, key=lambda w: (w < width, abs(w - width)))
        return f"{self.base}img/{files[best]}"

    def largest(self, stem: str) -> str:
        files = self.meta[stem]["files"]
        return f"{self.base}img/{files[max(files)]}"

    def tag(self, stem: str, alt: str, sizes: str = "100vw", cls: str = "", eager: bool = False, **attrs) -> Markup:
        if stem not in self.meta:
            raise KeyError(f"Image '{stem}' not found in src/img/")
        m = self.meta[stem]
        srcset = ", ".join(f"{self.base}img/{n} {w}w" for w, n in sorted(m["files"].items()))
        biggest = max(m["files"])
        h = round(m["h"] * biggest / m["w"])
        extra = "".join(f' {k.replace("_", "-")}="{escape(v)}"' for k, v in attrs.items())
        loading = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
        klass = f' class="{cls}"' if cls else ""
        return Markup(
            f'<img src="{self.src(stem, 960)}" srcset="{srcset}" sizes="{sizes}" width="{biggest}" height="{h}" '
            f'alt="{escape(alt)}"{klass} {loading}{extra}>'
        )


# ---------------------------------------------------------------- site
def load_content():
    site = json.loads((ROOT / "content" / "site.json").read_text())
    pieces = json.loads((ROOT / "content" / "pieces.json").read_text())
    cats = {c["id"]: c for c in site["categories"]}
    for i, p in enumerate(pieces):
        if p["category"] not in cats:
            sys.exit(f"Piece '{p['slug']}' has unknown category '{p['category']}'")
        p["cat"] = cats[p["category"]]
        p["cover"] = p["images"][0]
        p["path"] = f"work/{p['slug']}/"
    for c in site["categories"]:
        c["pieces"] = [p for p in pieces if p["category"] == c["id"]]
        c["path"] = f"{c['slug']}/"
    by_slug = {p["slug"]: p for p in pieces}
    site["featured_pieces"] = [by_slug[s] for s in site["featured"]]
    site["heroforge_pieces"] = [by_slug[s] for s in site["heroforge_pairs"]]
    return site, pieces


def file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()[:8]


def build(staging: bool, out: Path | None, make_zip: bool):
    base = "/staging/" if staging else "/"
    out = out or ROOT / ("dist-staging" if staging else "dist")
    print(f"Building {'STAGING' if staging else 'PRODUCTION'} -> {out.relative_to(ROOT)} (base {base})")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    site, pieces = load_content()
    images = Images(out, base)
    images.process_all()

    # static assets (css/js/icons) with cache-busting query strings
    shutil.copytree(ROOT / "static", out, dirs_exist_ok=True)
    (out / "video").mkdir(exist_ok=True)
    for f in SRC_VIDEO.iterdir():
        shutil.copy2(f, out / "video" / f.name)
    assets = {
        "css": f"{base}css/site.css?v={file_hash(ROOT / 'static/css/site.css')}",
        "js": f"{base}js/site.js?v={file_hash(ROOT / 'static/js/site.js')}",
    }

    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    abs_url = lambda path="": site["url"] + "/" + path.lstrip("/")  # noqa: E731
    env.globals.update(
        site=site,
        pieces=pieces,
        base=base,
        url=lambda path="": base + path.lstrip("/"),
        abs_url=abs_url,
        img=images.tag,
        img_src=images.src,
        img_large=images.largest,
        assets=assets,
        staging=staging,
        year=date.today().year,
    )

    pages: list[str] = []

    def render(template: str, path: str, **ctx):
        html = env.get_template(template).render(path=path, **ctx)
        target = out / (path + "index.html" if path.endswith("/") or path == "" else path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html)
        if template != "404.html" and "thanks" not in path:
            pages.append(path)

    default_og = images.og("banner-comic")
    render("home.html", "", og=default_og)
    render("gallery.html", "gallery/", current=None, items=pieces, og=default_og)
    for c in site["categories"]:
        render("gallery.html", c["path"], current=c, items=c["pieces"], og=images.og(c["cover"]))
    for i, p in enumerate(pieces):
        same = [q for q in pieces if q["category"] == p["category"] and q is not p]
        render(
            "piece.html", p["path"], piece=p,
            prev=pieces[i - 1], next=pieces[(i + 1) % len(pieces)],
            related=same[:4], og=images.og(p["cover"]),
        )
    render("process.html", "process/", og=images.og("process-printed-parts"))
    render("about.html", "about/", og=images.og("first-minis"))
    render("commissions.html", "commissions/", og=images.og("winged-warrior"))
    render("thanks.html", "commissions/thanks/", og=default_og)
    render("404.html", "404.html", og=default_og)

    # server + crawler files
    ctx = dict(base=base, site=site, staging=staging)
    (out / ".htaccess").write_text(env.get_template("htaccess.txt").render(**ctx))
    (out / "contact.php").write_text(env.get_template("contact.php.txt").render(**ctx))
    if staging:
        (out / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
    else:
        (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {abs_url('sitemap.xml')}\n")
        (out / "sitemap.xml").write_text(env.get_template("sitemap.xml").render(pages=pages, today=date.today().isoformat()))
    # the old WordPress /cosplay page is gone: keep a tiny redirect page as a no-.htaccess fallback
    render_redirect(out / "cosplay" / "index.html", base + "props-display/")

    n_files = sum(1 for f in out.rglob("*") if f.is_file())
    size = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    print(f"  pages: {len(pages)} | files: {n_files} | size: {size / 1_048_576:.1f} MB")

    if make_zip:
        zpath = ROOT / f"caseinpaint-{'staging' if staging else 'production'}.zip"
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(out.rglob("*")):
                if f.is_file():
                    z.write(f, f.relative_to(out))
        print(f"  zip: {zpath.name} ({zpath.stat().st_size / 1_048_576:.1f} MB)")


def render_redirect(target: Path, to: str):
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        f'<!doctype html><meta charset="utf-8"><title>Moved</title>'
        f'<meta name="robots" content="noindex"><link rel="canonical" href="{to}">'
        f'<meta http-equiv="refresh" content="0; url={to}"><a href="{to}">Props &amp; Display</a>\n'
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--staging", action="store_true", help="build for caseinpaint.net/staging/ (noindex)")
    ap.add_argument("--zip", action="store_true", help="also write a zip ready for Bluehost File Manager")
    ap.add_argument("--out", type=Path, help="output folder (default dist/ or dist-staging/)")
    a = ap.parse_args()
    build(a.staging, a.out, a.zip)
