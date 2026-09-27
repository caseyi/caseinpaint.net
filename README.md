# caseinpaint.net

Source for [caseinpaint.net](https://caseinpaint.net), Casey Iiams-Hauser's gallery of 3D printed and hand-painted minis, statues and props.

It is a small static site: plain HTML, one CSS file, one JS file, and a PHP form handler for the commission form. A Python script builds it from JSON content and Jinja templates, and makes responsive WebP images from the photos in `src/img/`. No WordPress, no plugins, nothing to patch.

## Quick start

```bash
pip install -r requirements.txt     # Pillow + Jinja2
python3 build.py                    # production build -> dist/
python3 build.py --staging --zip    # staging build -> dist-staging/ + caseinpaint-staging.zip
```

Preview locally (the form needs PHP, everything else works with any static server):

```bash
cd dist && python3 -m http.server 8000     # open http://localhost:8000
```

## Adding a new piece

1. Export a photo (JPG/PNG/WebP, ideally 1600 to 2400 px on the long side) into `src/img/`, named like `my-piece.webp`. Extra photos: `my-piece-2.webp`, `my-piece-3.webp`.
2. Add an entry to `content/pieces.json` (order in the file = order in the gallery):

   ```json
   {
     "slug": "my-piece",
     "title": "My Piece",
     "category": "tabletop",
     "images": ["my-piece", "my-piece-2"],
     "summary": "One or two sentences about it."
   }
   ```

   `category` is `statues`, `tabletop` or `props`. Add `"heroforge": "my-piece-heroforge"` to show a HeroForge before/after.
3. Optional: add the slug to `featured` in `content/site.json` to show it on the home page (keep 9 there so the grid stays even), or to `heroforge_pairs`.
4. `python3 build.py`, commit, deploy.

## Layout

| Path | What it is |
|---|---|
| `content/site.json` | Site settings, categories, featured pieces, studio links |
| `content/pieces.json` | Every gallery piece |
| `templates/` | Jinja page templates (`base.html` is the shared shell) |
| `templates/htaccess.txt` | Apache rules (HTTPS, old-URL redirects, caching) rendered into `.htaccess` |
| `templates/contact.php.txt` | Commission form mail handler rendered into `contact.php` |
| `static/` | CSS, JS and icons, copied as-is |
| `src/img/` | Web-sized photo masters (max 1800 px). The build makes 480/960/1600 px versions |
| `src/video/` | Resin printing time-lapse |
| `build.py` | The build script |

Full-resolution originals stay out of git (they live in `Documents/Case in Paint/v2`).

## Deploying

See [DEPLOY.md](DEPLOY.md).
