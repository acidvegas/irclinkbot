#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/dockerhub.py

import re

from fetch      import get_json
from formatting import BLUE, GREY, WHITE, ago, bold, clean, color, line, site_tag, stat, timestamp


TAG = site_tag('Docker Hub', WHITE, BLUE)


async def repository(session, match: re.Match) -> str | None:
	'''
	Parse a Docker Hub image link using the public API

	:param session: HTTP session
	:param match: Regex match with the namespace as group 1 (None for official images) & image name as group 2
	'''

	namespace = match.group(1) or 'library'
	data      = await get_json(session, f'https://hub.docker.com/v2/repositories/{namespace}/{match.group(2)}/')

	return line(TAG,
		bold(data['name'] if namespace == 'library' else f'{namespace}/{data["name"]}') + (color(' [official]', GREY) if namespace == 'library' else ''),
		clean(data['description'], 150) if data.get('description') else None,
		stat(data.get('pull_count', 0), 'pulls'),
		stat(data.get('star_count', 0), 'stars'),
		color('updated ', GREY) + ago(timestamp(data['last_updated'])) if data.get('last_updated') else None
	)


ROUTES = (
	(re.compile(r'https?://hub\.docker\.com/(?:_|r/([\w.-]+))/([\w.-]+)'), repository),
)
