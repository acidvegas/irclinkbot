#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/fourchan.py

import re

from fetch      import get_json
from formatting import CYAN, GREEN, GREY, WHITE, ago, bold, clean, color, line, site_tag, stat


TAG    = site_tag('4chan', WHITE, GREEN)
BOARDS = {} # Board -> worksafe flag, loaded once from the API


async def thread(session, match: re.Match) -> str | None:
	'''
	Parse a 4chan thread link using the public read-only API

	:param session: HTTP session
	:param match: Regex match with the board as group 1 & thread number as group 2
	'''

	board, number = match.groups()

	if not BOARDS:
		BOARDS.update({item['board']: bool(item['ws_board']) for item in (await get_json(session, 'https://a.4cdn.org/boards.json'))['boards']})

	op = (await get_json(session, f'https://a.4cdn.org/{board}/thread/{number}.json'))['posts'][0]

	return line(TAG,
		color(f'/{board}/', GREY) + ' ' + (bold(clean(op['sub'], 100)) + ' ' if op.get('sub') else '') + clean(op.get('com', ''), 200),
		color(clean(op.get('name', 'Anonymous'), 30), CYAN),
		stat(op.get('replies', 0), 'replies'),
		stat(op.get('images', 0), 'images'),
		color('archived', GREY) if op.get('archived') else None,
		ago(op['time']),
		nsfw=not BOARDS.get(board, True)
	)


ROUTES = (
	(re.compile(r'https?://boards\.(?:4chan|4channel)\.org/(\w+)/thread/(\d+)'), thread),
)
