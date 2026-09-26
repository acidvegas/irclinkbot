#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/gitea.py

import re

from fetch      import get_json
from formatting import BLUE, CYAN, GREEN, GREY, PURPLE, RED, WHITE, YELLOW, ago, bold, clean, color, line, site_tag, stat, timestamp


TAGS     = {'git.supernets.org': site_tag('SuperNETs Git', WHITE, CYAN), 'codeberg.org': site_tag('Codeberg', WHITE, BLUE)} # Gitea / Forgejo instances
RESERVED = ('admin', 'api', 'assets', 'explore', 'issues', 'milestones', 'notifications', 'org', 'pulls', 'repo', 'user')



async def issue(session, match: re.Match) -> str | None:
	'''
	Parse a Gitea issue or pull request link

	:param session: HTTP session
	:param match: Regex match with the host, owner, repo & number as groups 1-4
	'''

	host, owner, repo, number = match.groups()
	data                      = await get_json(session, f'https://{host}/api/v1/repos/{owner}/{repo}/issues/{number}')
	kind                = 'PR' if data.get('pull_request') else 'Issue'

	if (data.get('pull_request') or {}).get('merged'):
		state = color('merged', PURPLE)
	elif data['state'] == 'open':
		state = color('open', GREEN)
	else:
		state = color('closed', RED)

	return line(TAGS[host],
		color(f'{owner}/{repo} {kind} #{number}', GREY) + ' ' + bold(clean(data['title'], 200)),
		state,
		color(data['user']['login'], CYAN),
		stat(data.get('comments', 0), 'comments'),
		ago(timestamp(data['created_at']))
	)


async def repository(session, match: re.Match) -> str | None:
	'''
	Parse a Gitea repository link (also used for any deeper path within a repository)

	:param session: HTTP session
	:param match: Regex match with the host, owner & repo as groups 1-3
	'''

	host, owner, repo = match.groups()

	if owner.lower() in RESERVED:
		return

	data = await get_json(session, f'https://{host}/api/v1/repos/{owner}/{repo.removesuffix(".git")}')

	return line(TAGS[host],
		bold(data['full_name']),
		clean(data['description'], 150) if data.get('description') else None,
		color(data['language'], YELLOW) if data.get('language') else None,
		stat(data.get('stars_count', 0), 'stars'),
		stat(data.get('forks_count', 0), 'forks'),
		stat(data.get('open_issues_count', 0), 'issues'),
		color('updated ', GREY) + ago(timestamp(data['updated_at'])) if data.get('updated_at') else None,
		color('archived', RED) if data.get('archived') else None
	)


async def user(session, match: re.Match) -> str | None:
	'''
	Parse a Gitea user or organization link

	:param session: HTTP session
	:param match: Regex match with the host & username as groups 1-2
	'''

	host, username = match.groups()

	if username.lower() in RESERVED:
		return

	data = await get_json(session, f'https://{host}/api/v1/users/{username}')
	name = color(clean(data['full_name'], 50), CYAN) + color(f' ({data["login"]})', GREY) if data.get('full_name') else color(data['login'], CYAN)

	return line(TAGS[host],
		name,
		clean(data['description'], 150) if data.get('description') else None,
		stat(data.get('followers_count', 0), 'followers')
	)


ROUTES = (
	(re.compile(r'https?://(git\.supernets\.org|codeberg\.org)/([\w.-]+)/([\w.-]+)/(?:issues|pulls)/(\d+)'), issue),
	(re.compile(r'https?://(git\.supernets\.org|codeberg\.org)/([\w.-]+)/([\w.-]+?)(?:[/?#].*)?$'),          repository),
	(re.compile(r'https?://(git\.supernets\.org|codeberg\.org)/([\w.-]+)/?(?:[?#].*)?$'),                    user),
)
