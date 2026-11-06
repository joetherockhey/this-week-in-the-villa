"""Weekly trend research, delegated to free LLMs via a local FreeLLMAPI router.

Claude plans and reviews; the free models read the source pages.
Usage: python tools/research.py   ->  writes data/raw/*.json and data/trends.draft.json
"""
import json, re, sys, html, urllib.request, datetime, pathlib
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
API = "http://localhost:31415/v1/chat/completions"
KEY = pathlib.Path(r"C:\Users\josep\Projects\freellmapi\.unified-key").read_text().strip()
TODAY = datetime.date.today()

SOURCES = [
    "https://newengen.com/insights/tiktok-trends/",
    "https://newengen.com/insights/october-tiktok-trends/",
    "https://www.gelato.com/blog/tiktok-trends-right-now",
    "https://www.socialpilot.co/blog/instagram-reels-trends",
    "https://later.com/blog/tiktok-trends/",
    "https://later.com/blog/instagram-reels-trends/",
    "https://ramd.am/blog/trends-tiktok",
    "https://www.takema-studio.com/marques/trends-tiktok-octobre-2026",
    "https://insights.vaizle.com/instagram-reel-trends/",
    "https://www.anijam.ai/blog/instagram-reels-trends/",
] + sys.argv[1:]


class Text(HTMLParser):
    """HTML -> text, keeping link targets inline so the model can cite real URLs."""
    def __init__(self):
        super().__init__(); self.out = []; self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "footer", "svg"): self.skip += 1
        if tag == "a":
            href = dict(attrs).get("href") or ""
            if re.match(r"https://(www\.)?(tiktok|instagram|youtube|youtu\.be|x\.com|twitter)", href):
                self.out.append(f" [{href}] ")
        if tag in ("p", "h1", "h2", "h3", "h4", "li", "br"): self.out.append("\n")
    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "footer", "svg") and self.skip: self.skip -= 1
    def handle_data(self, d):
        if not self.skip: self.out.append(d)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0"})
    raw = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    p = Text(); p.feed(raw)
    # embedded TikTok/IG blockquotes keep their URL in cite=""; grab those too
    embeds = set(re.findall(r'cite="(https://www\.(?:tiktok|instagram)\.com/[^"]+)"', raw))
    text = re.sub(r"\n\s*\n+", "\n", html.unescape("".join(p.out)))
    return text[:30000], sorted(embeds)


MODELS = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash", "auto"]


def ask(prompt):
    # free tiers 429 often; walk down the list, the router's "auto" is the last resort
    for i, model in enumerate(MODELS):
        body = json.dumps({"model": model, "temperature": 0.2,
                           "messages": [{"role": "user", "content": prompt}]}).encode()
        req = urllib.request.Request(API, body, {"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
        try:
            r = json.load(urllib.request.urlopen(req, timeout=300))
            return r["choices"][0]["message"]["content"], r.get("model")
        except urllib.error.HTTPError as e:
            if i == len(MODELS) - 1: raise
            print(f"    {model}: HTTP {e.code}, trying next")


def as_json(s):
    m = re.search(r"\[.*\]|\{.*\}", s, re.S)
    return json.loads(m.group(0))


EXTRACT = """Today is {today}. Below is the text of a social media trend roundup page ({url}).
Extract every individual trend, format, meme, sound or challenge it describes.
Return ONLY a JSON array; each item:
{{"name": str, "platforms": [str], "what": "1-2 sentence plain description of what people do",
  "format": "reel/video format in a few words", "sound": str or null,
  "examples": [real URLs copied exactly from the text, tiktok/instagram/youtube only; never invent],
  "dated": "the date or month the page attaches to this trend, or null",
  "source": "{url}"}}
Skip anything the page dates before {cutoff}. Embedded post URLs on the page: {embeds}

PAGE TEXT:
{text}"""

MERGE = """Today is {today}. You are helping a Sydney full-service creative agency brief its
social team on THIS WEEK's social trends. Below are trends extracted from several roundup pages.

1. Merge duplicates (same trend under different names).
2. Drop anything stale (clearly older than ~4 weeks) or that a brand could not plausibly use
   (tragedy, politics, crude or adult content, trends that only work for individual creators).
3. Rank the remaining by how current and how brand-usable they are. Keep the best 15-20.
Return ONLY a JSON array; each item:
{{"name": str, "platforms": [str], "what": str, "format": str, "sound": str or null,
  "why_now": "one sentence on why it is hot this week",
  "brand_use": "2-3 sentences: a concrete way a brand or one of the agency's clients could run it",
  "example_brief": "one-line example concept, e.g. 'A coffee brand uses X to ...'",
  "risk": "one short caution, or null",
  "examples": [URLs from the input only], "sources": [source URLs]}}

INPUT:
{items}"""


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    cutoff = TODAY - datetime.timedelta(days=35)
    found = []
    if "--merge" in sys.argv:  # reuse data/raw, skip fetching
        found = [i for f in sorted(RAW.glob("*.json")) for i in json.loads(f.read_text("utf-8"))["items"]]
    for url in [] if found else SOURCES:
        slug = re.sub(r"\W+", "-", url.split("//")[1]).strip("-")[:60]
        try:
            text, embeds = fetch(url)
            reply, model = ask(EXTRACT.format(today=TODAY, cutoff=cutoff, url=url, embeds=embeds, text=text))
            items = as_json(reply)
            (RAW / f"{slug}.json").write_text(json.dumps({"model": model, "items": items}, indent=1), "utf-8")
            print(f"{len(items):3} trends  {model:30}  {url}")
            found += items
        except Exception as e:
            print(f"  fail  {url}: {e}")
    reply, model = ask(MERGE.format(today=TODAY, items=json.dumps(found)))
    out = as_json(reply)
    (ROOT / "data" / "trends.draft.json").write_text(json.dumps(out, indent=1), "utf-8")
    print(f"merged -> {len(out)} trends via {model}")


if __name__ == "__main__":
    main()
