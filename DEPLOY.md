# Deploying to Bluehost

The live site is still WordPress. The plan is to preview the new static site at **caseinpaint.net/staging/** first, then swap it in.

## 1. Upload the staging preview

The staging build uses `/staging/` in every link, adds `noindex` so search engines skip it, and shows a yellow "Staging preview" banner.

1. Build it (or use the zip that is already built): `python3 build.py --staging --zip`
2. Bluehost > **Websites** > caseinpaint.net > **File Manager** (or cPanel > File Manager).
3. Open `public_html/`, create a folder named `staging`, open it.
4. **Upload** `caseinpaint-staging.zip`, then right-click it > **Extract** into `public_html/staging/`. Delete the zip afterwards.
   - The zip contains a hidden `.htaccess`. In File Manager, Settings > "Show hidden files" to see it.
5. Visit https://caseinpaint.net/staging/ and click around.
6. Test the form on `/staging/commissions/`. It sends to casey@caseinpaint.net using PHP `mail()`. If nothing arrives, check spam, then check that the casey@caseinpaint.net mailbox exists in Bluehost Email (the handler sends *from* that address).

WordPress keeps running at the root the whole time. The staging folder has its own `.htaccess`, so WordPress rewrite rules do not interfere.

## 2. Go live (when you're happy)

1. **Back up WordPress first.** In File Manager, select everything in `public_html/` except `staging/`, compress it to `wordpress-backup-YYYY-MM-DD.zip`, and download it. Also export the database from cPanel > phpMyAdmin (or use Bluehost's backup tool) if you might want WordPress back.
2. Move the WordPress files out of `public_html/` (for example into a new folder next to it, `~/wordpress-old/`). Keep `public_html/.well-known/` if it exists (SSL certificate validation uses it).
3. Build production: `python3 build.py --zip` (makes `caseinpaint-production.zip`).
4. Upload `caseinpaint-production.zip` to `public_html/` and extract it there.
5. Check https://caseinpaint.net/ and a couple of old URLs:
   - `/commissions` > new commissions page
   - `/tabletop-gaming` and `/statues-busts` > category pages (same URLs as before)
   - `/cosplay` > redirects to `/props-display/`
6. Delete `public_html/staging/` once production is up.
7. In Google Search Console (if you use it), submit `https://caseinpaint.net/sitemap.xml`.

## Updating later

Edit content, run `python3 build.py --zip`, upload the zip to `public_html/`, extract, overwrite. Or upload just the changed files.

## Rolling back

Move the static files out of `public_html/` and move the WordPress files back in.
