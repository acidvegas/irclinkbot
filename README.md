# IRC Link Bot

One bot for link titles and metadata, so channels do not need ten bots doing the same thing. Pure Python IRC with asyncio, [aiohttp](https://pypi.org/project/aiohttp/) for fetching links, and no API keys.

## Setup
```
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python linkbot.py
```

Use `-d` / `--debug` to join `#dev` instead of `#superbowl` with debug logging.

To identify with NickServ on connect, create a `.env` next to the script:
```
NICKSERV_PASSWORD=yourpassword
```

## Commands
| Command              | Who                | Description                                |
|----------------------|--------------------|--------------------------------------------|
| `@link`              | Anyone, in channel | Show bot info *(10s cooldown per channel)* |
| `.raw <line>`        | Admin, in PM       | Send a raw line to the server              |
| `@link ignore +nick` | Admin, in PM       | Ignore a nick                              |
| `@link ignore -nick` | Admin, in PM       | Stop ignoring a nick                       |

The ignore list is saved to `ignore.json`. Messages sent to the bot in PM are not parsed.

## Behavior
- Connects to `irc.supernets.org` on port 6697 with TLS, reconnects 15 seconds after a disconnect
- Joins 6 seconds after connecting, rejoins 3 seconds after a kick, rejoins when invited
- Retries every 15 seconds when banned, invite only, full, etc.
- Parses the first link in each channel message, following redirects *(t.co, bit.ly, etc)*
- Rate limited to 5 links per 60 seconds
- Caches the last 1000 links for an hour, and stays quiet when the same link is repeated in a channel within 10 minutes
- Output is capped at 400 bytes per line, with control, zero-width, and bidi characters stripped
- Pages that only return a bot check *(Cloudflare, captchas, etc)* are skipped

## Parsers
| Site                     | Links                                           | Shows                                                          |
|--------------------------|-------------------------------------------------|----------------------------------------------------------------|
| Amazon                   | amazon.* product pages                          | Title, price, rating                                           |
| Apple Music / Podcasts   | music.apple.com, podcasts.apple.com             | Track, album, artist, length, genre, year, episodes            |
| arXiv                    | arxiv.org abs & pdf                             | Title, authors, category, date                                 |
| Bandcamp                 | *.bandcamp.com albums & tracks                  | Title, artist, tracks, length, year                            |
| Bluesky                  | bsky.app posts & profiles                       | Author, text, replies, reposts, likes, followers               |
| 4chan                    | boards.4chan.org threads                        | Board, subject, OP text, replies, images                       |
| Codeberg / SuperNETs Git | Repos, issues, pulls, users                     | Description, language, stars, forks, issues, state             |
| CVE                      | cve.org, nvd.nist.gov, cve.mitre.org            | CVSS score & severity, summary, published date                 |
| Dailymotion              | dailymotion.com, dai.ly                         | Title, owner, length, views, likes                             |
| Discord                  | discord.gg & discord.com invites                | Server, description, members, online                           |
| Docker Hub               | hub.docker.com images                           | Description, pulls, stars, last updated                        |
| eBay                     | ebay.* listings                                 | Title, price, condition                                        |
| Etsy                     | etsy.com listings                               | Title, shop, price, rating                                     |
| GitHub                   | Repos, issues, PRs, commits, users, orgs, gists | Description, language, stars, forks, state, diff stats         |
| GitLab                   | gitlab.com projects, issues, merge requests     | Description, stars, forks, state, comments                     |
| Goodreads                | goodreads.com books                             | Title, authors, rating, pages                                  |
| Hacker News              | Stories, comments, users                        | Title, domain, points, comments, karma                         |
| Hugging Face             | Models, datasets, spaces                        | Task, downloads, likes, status                                 |
| IMDb                     | imdb.com titles                                 | Year, type, rating, runtime, genres, plot                      |
| Imgur                    | Posts, albums, galleries                        | Title, images, views, upvotes, comments                        |
| Instagram                | Posts, reels, profiles                          | Author, caption, likes, comments, followers                    |
| Kick                     | kick.com channels                               | Live title, category, viewers, uptime, followers               |
| Lemmy                    | Any instance post                               | Community, title, author, score, comments                      |
| Letterboxd               | letterboxd.com films                            | Year, rating, director, genres                                 |
| Lobsters                 | lobste.rs stories                               | Title, tags, score, submitter, comments                        |
| Mastodon                 | Any instance status                             | Author, text, replies, boosts, favs                            |
| npm / PyPI / crates.io   | Package pages                                   | Version, description, license, downloads                       |
| Reddit                   | Posts, redd.it, subreddits, users               | Subreddit, title, author, score, comments                      |
| SoundCloud               | Tracks, sets, users                             | Artist, length, plays, likes, comments, genre                  |
| Spotify                  | Tracks, albums, artists, playlists, podcasts    | Title, artist, type, year                                      |
| Steam                    | Store & community app pages                     | Price, discount, reviews, genres, developer                    |
| Telegram                 | t.me channels & posts                           | Post text, views, subscribers                                  |
| Threads                  | Posts & profiles                                | Author, text, followers                                        |
| TikTok                   | Videos                                          | Author, caption, length, views, likes, comments                |
| Twitch                   | Channels, VODs, clips                           | Live title, game, viewers, uptime, followers                   |
| Vimeo                    | Videos                                          | Title, uploader, length, date                                  |
| Wayback Machine          | web.archive.org snapshots                       | Archived title, original site, snapshot date                   |
| Wikipedia                | Any language, mobile included                   | Title, short description, summary                              |
| X / Twitter              | Posts & profiles, fx/vx mirrors included        | Author, text, replies, RTs, likes, views, media                |
| YouTube                  | Videos, shorts, live, youtu.be                  | Title, channel, length, views, likes, comments, date           |
| Generic                  | Everything else                                 | Mime type, title, size, domain *(image dimensions for images)* |

Each site is a module in `parsers/`. To add one, create a module with a `ROUTES` tuple of `(regex, handler)` pairs and add it to `THEMED` in `parsers/__init__.py`.

Some sites block datacenter IPs. Reddit falls back to basic post info, and eBay / Etsy may not work from a VPS.

