#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/youtube.py

import asyncio
import json
import re

from fetch      import get_json
from formatting import CYAN, GREY, RED, WHITE, bold, clean, color, line, runtime, site_tag, stat


TAG     = site_tag('YouTube', WHITE, RED)
CONTEXT = {'client': {'clientName': 'WEB', 'clientVersion': '2.20250101.00.00', 'hl': 'en', 'gl': 'US'}}


async def video(session, match: re.Match) -> str | None:
	'''
	Parse a YouTube video link using the public InnerTube API (no API key required)

	:param session: HTTP session
	:param match: Regex match with the video id as group 1
	'''

	video_id    = match.group(1)
	player, nxt = await asyncio.gather(
		get_json(session, 'https://www.youtube.com/youtubei/v1/player?prettyPrint=false', json={'videoId': video_id, 'context': CONTEXT}),
		get_json(session, 'https://www.youtube.com/youtubei/v1/next?prettyPrint=false',   json={'videoId': video_id, 'context': CONTEXT})
	)

	if not (details := player.get('videoDetails')):
		data = await get_json(session, f'https://www.youtube.com/oembed?format=json&url=https://www.youtube.com/watch?v={video_id}')
		return line(TAG, bold(clean(data['title'])), color(clean(data['author_name'], 50), CYAN))

	micro  = player.get('microformat', {}).get('playerMicroformatRenderer', {})
	nxt    = json.dumps(nxt)
	likes  = re.search(r'like this video along with ([\d,]+) other', nxt)
	counts = re.search(r'engagement-panel-comments-section".{0,400}?"contextualInfo": \{"runs": \[\{"text": "([^"]+)"', nxt)
	length = color('LIVE', RED) if details.get('isLive') else runtime(details.get('lengthSeconds', 0))

	return line(TAG,
		bold(clean(details['title'])),
		color(clean(details['author'], 50), CYAN),
		length,
		stat(details.get('viewCount', 0), 'views'),
		stat(likes.group(1).replace(',', ''), 'likes') if likes else None,
		stat(counts.group(1), 'comments') if counts else None,
		color(micro['publishDate'][:10], GREY) if micro.get('publishDate') else None,
		nsfw=micro.get('isFamilySafe') is False
	)


ROUTES = (
	(re.compile(r'https?://(?:(?:www|m|music)\.)?youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|live/|embed/|v/)([\w-]{11})'), video),
	(re.compile(r'https?://(?:www\.)?youtu\.be/([\w-]{11})'),                                                           video),
)
