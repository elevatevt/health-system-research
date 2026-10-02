"""Download raw source files into data/raw (gitignored). Skips files already present.

ahrq.gov returns an empty 202 to bare scripted requests; browser-like headers work.
"""
import sys
import urllib.request

from common import RAW, SOURCES

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.ahrq.gov/chsp/data-resources/compendium-2023.html",
}


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    for key, src in SOURCES.items():
        dest = RAW / src["file"]
        if dest.exists() and dest.stat().st_size > 0:
            print(f"have  {dest.name}")
            continue
        req = urllib.request.Request(src["url"], headers=HEADERS)
        with urllib.request.urlopen(req, timeout=300) as r:
            body = r.read()
        # AHRQ's WAF answers some requests with an empty body or an HTML challenge page.
        if not body or body.lstrip()[:15].lower().startswith((b"<!doctype html", b"<html")):
            print(f"BLOCKED {src['url']} (status {r.status}); download it in a browser to {dest}", file=sys.stderr)
            return 1
        dest.write_bytes(body)
        print(f"got   {dest.name} ({len(body):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
