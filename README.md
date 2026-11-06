# This Week in the Villa: social trend report

Weekly list of brand-usable TikTok / Instagram / YouTube trends.
Live: https://joetherockhey.github.io/this-week-in-the-villa/

Weekly run (Wednesdays, from the Trend report button on Claude HQ's Run tab, which starts the `/trend-report` skill):

1. Research: Claude (Opus) reads the latest round-ups and TikTok sound pages and writes `data/trends.json`
   (what, origin, usage + usage_n, sound, longevity evergreen/seasonal, brand use, examples with verified plays/likes, sources).
   Keep the file in rank order: evergreen first, then seasonal, each by usage_n. Example 1 must be the origin or top post on the
   trend's actual sound (check the post page's music id). Per-batch research notes live in `data/research/`. `tools/find_examples.cjs` pulls recent
   example posts from TikTok discover/sound pages; `tools/oembed.py` dates them.
   `tools/research.py` is the older free-LLM (FreeLLMAPI) extraction pass, kept as an optional first sweep.
2. `node tools/shots.cjs` grabs one example image per trend (TikTok cover frame / Instagram embed).
3. `python tools/ai_images.py` fills any gaps with a labelled AI illustration (Cloudflare Workers AI, free tier).
4. `python tools/words.py` pulls Wiktionary lookups for `data/words.json` and works out each word's status.
5. `python tools/build.py` writes `index.html`, freezes the week in `archive/<monday>/` and rebuilds `archive/index.html` (past reports + trend history; trends match across weeks by exact name, so keep names stable). Review, then push.
6. Write `data/deck/<monday>.json` (the deck's words), `python tools/deck.py` prints the Slides requests, and the deck is a copy of the Drive template. Each deck's link goes in `data/decks.json`, and `python tools/build.py` lists them on `slides/`.
