#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/youtube.py

import asyncio
import datetime
import json
import re

from fetch      import get_json
from formatting import CYAN, GREY, RED, WHITE, bold, clean, color, line, runtime, site_tag, stat


TAG     = site_tag('YouTube', WHITE, RED)
CONTEXT = {'client': {'clientName': 'WEB', 'clientVersion': '2.20250101.00.00', 'hl': 'en', 'gl': 'US'}}
MUSIC   = {'client': {'clientName': 'WEB_REMIX', 'clientVersion': '1.20250101.01.00', 'hl': 'en', 'gl': 'US'}} # YouTube Music web client, still returns video details when YouTube asks datacenter IPs to sign in


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

	if not player.get('videoDetails'):
		player = await get_json(session, 'https://www.youtube.com/youtubei/v1/player?prettyPrint=false', json={'videoId': video_id, 'context': MUSIC})

	micro  = player.get('microformat', {}).get('playerMicroformatRenderer', {})
	nxt    = json.dumps(nxt)
	likes  = re.search(r'like this video along with ([\d,]+) other', nxt)
	counts = re.search(r'engagement-panel-comments-section".{0,400}?"contextualInfo": \{"runs": \[\{"text": "([^"]+)"', nxt)
	views  = re.search(r'"viewCount": \{"simpleText": "([\d,]+) views"', nxt)
	date   = micro.get('publishDate', '')[:10]

	if not date and (text := re.search(r'"dateText": \{"simpleText": "([^"]+)"', nxt)):
		try:
			date = datetime.datetime.strptime(text.group(1).removeprefix('Premiered ').removeprefix('Streamed live on '), '%b %d, %Y').strftime('%Y-%m-%d')
		except ValueError:
			date = text.group(1)

	if details := player.get('videoDetails'):
		title, author = details['title'], details['author']
		length        = color('LIVE', RED) if details.get('isLive') else runtime(details.get('lengthSeconds', 0))
		view_count    = details.get('viewCount', 0)
	else: # Both player clients were refused, so use oEmbed for the title & channel and skip the length
		data          = await get_json(session, f'https://www.youtube.com/oembed?format=json&url=https://www.youtube.com/watch?v={video_id}')
		title, author = data['title'], data['author_name']
		length        = None
		view_count    = views.group(1).replace(',', '') if views else None

	return line(TAG,
		bold(clean(title)),
		color(clean(author, 50), CYAN),
		length,
		stat(view_count, 'views') if view_count is not None else None,
		stat(likes.group(1).replace(',', ''), 'likes') if likes else None,
		stat(counts.group(1), 'comments') if counts else None,
		color(date, GREY) if date else None,
		nsfw=micro.get('isFamilySafe') is False
	)

ROUTES = (
	(re.compile(r'https?://(?:(?:www|m|music)\.)?youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|live/|embed/|v/)([\w-]{11})'), video),
	(re.compile(r'https?://(?:www\.)?youtu\.be/([\w-]{11})'),                                                           video),
)
