#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/packages.py

import asyncio
import re

from fetch      import BOT_UA, get_json
from formatting import BLUE, BROWN, GREY, RED, WHITE, YELLOW, bold, clean, color, line, site_tag, stat


async def crates(session, match: re.Match) -> str | None:
	'''
	Parse a crates.io package link (crates.io requires an identifying User-Agent)

	:param session: HTTP session
	:param match: Regex match with the crate name as group 1
	'''

	data = (await get_json(session, f'https://crates.io/api/v1/crates/{match.group(1)}', headers={'User-Agent': BOT_UA}))['crate']

	return line(site_tag('crates.io', WHITE, BROWN),
		bold(data['name']) + ' ' + color(data.get('max_stable_version') or data['max_version'], GREY),
		clean(data.get('description') or '', 200),
		stat(data.get('downloads', 0), 'downloads'),
		stat(data.get('recent_downloads') or 0, 'recent')
	)


async def npm(session, match: re.Match) -> str | None:
	'''
	Parse an npm package link

	:param session: HTTP session
	:param match: Regex match with the package name as group 1
	'''

	name            = match.group(1)
	data, downloads = await asyncio.gather(get_json(session, f'https://registry.npmjs.org/{name}/latest'), get_json(session, f'https://api.npmjs.org/downloads/point/last-week/{name}'), return_exceptions=True)

	if isinstance(data, Exception):
		raise data

	downloads = None if isinstance(downloads, Exception) else downloads.get('downloads')

	return line(site_tag('npm', WHITE, RED),
		bold(data['name']) + ' ' + color(data['version'], GREY),
		clean(data.get('description') or '', 200),
		data['license'] if isinstance(data.get('license'), str) else None,
		stat(downloads, 'weekly downloads') if downloads is not None else None
	)


async def pypi(session, match: re.Match) -> str | None:
	'''
	Parse a PyPI package link

	:param session: HTTP session
	:param match: Regex match with the package name as group 1
	'''

	info    = (await get_json(session, f'https://pypi.org/pypi/{match.group(1)}/json'))['info']
	license = info.get('license_expression') or info.get('license') or ''

	return line(site_tag('PyPI', YELLOW, BLUE),
		bold(info['name']) + ' ' + color(info['version'], GREY),
		clean(info.get('summary') or '', 200),
		clean(license, 30) if license and '\n' not in license else None,
		color(f'python {info["requires_python"]}', GREY) if info.get('requires_python') else None
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.)?pypi\.org/project/([\w.-]+)'),                  pypi),
	(re.compile(r'https?://(?:www\.)?npmjs\.com/package/((?:@[\w.-]+/)?[\w.-]+)'),  npm),
	(re.compile(r'https?://(?:www\.)?crates\.io/crates/([\w-]+)'),                   crates),
	(re.compile(r'https?://(?:www\.)?lib\.rs/crates/([\w-]+)'),                      crates),
)
