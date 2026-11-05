# Apparent social trend report

Weekly list of brand-usable TikTok / Instagram / YouTube trends, styled after apparent.com.au.
Live: https://joetherockhey.github.io/apparent-trends/

Weekly run (Mondays):

1. Research: Claude (Opus) reads the latest round-ups and TikTok sound pages and writes `data/trends.json`
   (what, origin, usage + usage_n, sound, longevity evergreen/seasonal, brand use, examples with verified plays/likes, sources).
   Keep the file in rank order: evergreen first, then seasonal, each by usage_n. Example 1 must be the origin or top post on the
   trend's actual sound (check the post page's music id). Per-batch research notes live in `data/research/`. `tools/find_examples.cjs` pulls recent
   example posts from TikTok discover/sound pages; `tools/oembed.py` dates them.
   `tools/research.py` is the older free-LLM (FreeLLMAPI) extraction pass, kept as an optional first sweep.
2. `node tools/shots.cjs` grabs one example image per trend (TikTok cover frame / Instagram embed).
3. `python tools/ai_images.py` fills any gaps with a labelled AI illustration (Cloudflare Workers AI, free tier).
4. `python tools/build.py` writes `index.html`, freezes the week in `archive/<monday>/` and rebuilds `archive/index.html` (past reports + trend history; trends match across weeks by exact name, so keep names stable). Review, then push.
