#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/discord.py

import re

from fetch      import get_json
from formatting import BLUE, GREY, WHITE, bold, clean, color, line, site_tag, stat


TAG = site_tag('Discord', WHITE, BLUE)


async def invite(session, match: re.Match) -> str | None:
	'''
	Parse a Discord invite link using the public invite API (no authentication required)

	:param session: HTTP session
	:param match: Regex match with the invite code as group 1
	'''

	data  = await get_json(session, f'https://discord.com/api/v10/invites/{match.group(1)}?with_counts=true')
	guild = data.get('guild') or {}

	return line(TAG,
		bold(clean(guild.get('name') or (data.get('channel') or {}).get('name', 'Group DM'), 100)),
		clean(guild['description'], 150) if guild.get('description') else None,
		stat(data.get('approximate_member_count', 0), 'members'),
		stat(data.get('approximate_presence_count', 0), 'online'),
		color('#' + data['channel']['name'], GREY) if (data.get('channel') or {}).get('name') and guild else None,
		nsfw=guild.get('nsfw_level') in (1, 3)
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.)?(?:discord\.gg|discord(?:app)?\.com/invite)/([\w-]+)'), invite),
)
