#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/lobsters.py

import re

from fetch      import get_json
from formatting import CYAN, GREY, RED, WHITE, ago, bold, clean, color, line, site_tag, stat, timestamp


TAG = site_tag('Lobsters', WHITE, RED)


async def story(session, match: re.Match) -> str | None:
	'''
	Parse a Lobsters story link using the public JSON endpoint

	:param session: HTTP session
	:param match: Regex match with the story short id as group 1
	'''

	data      = await get_json(session, f'https://lobste.rs/s/{match.group(1)}.json')
	submitter = data.get('submitter_user')
	submitter = submitter.get('username', '') if isinstance(submitter, dict) else submitter

	return line(TAG,
		bold(clean(data['title'], 250)),
		color(' '.join(data.get('tags', [])), GREY) if data.get('tags') else None,
		stat(data.get('score', 0), 'points'),
		color(submitter, CYAN) if submitter else None,
		stat(data.get('comment_count', 0), 'comments'),
		ago(timestamp(data['created_at'])) if data.get('created_at') else None
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.)?lobste\.rs/s/(\w+)'), story),
)
