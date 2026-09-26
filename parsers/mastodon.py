#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/mastodon.py

import re

from fetch      import get_json
from formatting import BLUE, CYAN, GREY, WHITE, ago, clean, color, line, site_tag, stat, timestamp


TAG = site_tag('Mastodon', WHITE, BLUE)


async def status(session, match: re.Match) -> str | None:
	'''
	Parse a Mastodon (or compatible fediverse server) status link using the server's public API (no API key required)

	:param session: HTTP session
	:param match: Regex match with the host as group 1 & status id as group 2
	'''

	host    = match.group(1)
	toot    = await get_json(session, f'https://{host}/api/v1/statuses/{match.group(2)}')
	account = toot['account']
	acct    = account['acct'] if '@' in account['acct'] else f'{account["acct"]}@{host}'
	text    = color('CW: ' + clean(toot['spoiler_text'], 150), GREY) if toot.get('spoiler_text') else clean(toot.get('content', ''), 220)
	stamp   = timestamp(toot['created_at']) if toot.get('created_at') else None
	media   = len(toot.get('media_attachments', []))

	return line(TAG,
		color(clean(account.get('display_name') or account['username'], 50), CYAN) + color(f' (@{acct})', GREY) + ': ' + text,
		stat(toot.get('replies_count', 0), 'replies'),
		stat(toot.get('reblogs_count', 0), 'boosts'),
		stat(toot.get('favourites_count', 0), 'favs'),
		color(f'{media} attachment' + ('s' if media > 1 else ''), GREY) if media else None,
		ago(stamp) if stamp else None,
		nsfw=bool(toot.get('sensitive'))
	)


ROUTES = (
	(re.compile(r'https?://([\w.-]+\.[a-z]{2,})/@\w+(?:@[\w.-]+)?/(\d+)/?(?:[?#].*)?$'), status),
)
