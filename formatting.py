#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# formatting.py

import datetime
import html
import re
import time


BOLD  = '\x02'
COLOR = '\x03'
RESET = '\x0f'

WHITE      = '00'
BLACK      = '01'
BLUE       = '02'
GREEN      = '03'
RED        = '04'
BROWN      = '05'
PURPLE     = '06'
ORANGE     = '07'
YELLOW     = '08'
LIGHTGREEN = '09'
CYAN       = '10'
LIGHTCYAN  = '11'
LIGHTBLUE  = '12'
PINK       = '13'
GREY       = '14'
LIGHTGREY  = '15'

SEP = f' {COLOR}{GREY}|{COLOR} '

MAX_BYTES = 400 # Max bytes of a single output line (leaves room for the 'PRIVMSG #channel :' prefix)

INVISIBLE = re.compile(r'[\x00-\x1f\x7f\u200b\u200e\u200f\u202a-\u202e\u2066-\u2069\ufeff]') # Control, zero-width & bidi override characters (ZWJ kept for emoji sequences)

STATS = { # Stat label -> (icon, number color), so the same kind of stat looks the same on every site
	'views'            : ('👁', LIGHTCYAN),
	'plays'            : ('▶', LIGHTCYAN),
	'viewers'          : ('👁', LIGHTCYAN),
	'downloads'        : ('⬇', LIGHTCYAN),
	'weekly downloads' : ('⬇', LIGHTCYAN),
	'recent'           : ('⬇', LIGHTCYAN),
	'pulls'            : ('⬇', LIGHTCYAN),
	'likes'            : ('👍', GREEN),
	'favs'             : ('❤', GREEN),
	'stars'            : ('⭐', GREEN),
	'points'           : ('▲', GREEN),
	'upvotes'          : ('▲', GREEN),
	'karma'            : ('▲', GREEN),
	'post karma'       : ('▲', GREEN),
	'comment karma'    : ('▲', GREEN),
	'comments'         : ('💬', YELLOW),
	'replies'          : ('💬', YELLOW),
	'RTs'              : ('🔁', PURPLE),
	'reposts'          : ('🔁', PURPLE),
	'boosts'           : ('🔁', PURPLE),
	'shares'           : ('🔗', PURPLE),
	'followers'        : ('👥', LIGHTBLUE),
	'members'          : ('👥', LIGHTBLUE),
	'online'           : ('🟢', LIGHTBLUE),
	'forks'            : ('🍴', None),
	'issues'           : ('🐛', None),
	'repos'            : ('📦', None),
	'files'            : ('📄', None),
	'tracks'           : ('🎵', None),
	'episodes'         : ('🎙', None),
	'images'           : ('🖼', None),
	'tweets'           : ('📝', None),
	'posts'            : ('📝', None)
}


def ago(timestamp: float) -> str:
	'''
	Convert a unix timestamp into a short relative age string

	:param timestamp: Unix timestamp
	'''

	seconds = max(0, int(time.time() - timestamp))

	for unit, size in (('y', 31_536_000), ('mo', 2_592_000), ('d', 86_400), ('h', 3600), ('m', 60)):
		if seconds >= size:
			return color(f'{seconds // size}{unit} ago', GREY)

	return color(f'{seconds}s ago', GREY)


def bold(text: str) -> str:
	'''
	Make text bold

	:param text: Text to make bold
	'''

	return f'{BOLD}{text}{BOLD}'


def clean(text: str, limit: int = 200) -> str:
	'''
	Strip HTML, entities, control characters & excess whitespace from text, then truncate it

	:param text: Text to clean
	:param limit: Maximum length of the returned text
	'''

	text = html.unescape(re.sub(r'<[^>]+>', ' ', str(text)))
	text = INVISIBLE.sub(' ', text)
	text = ' '.join(text.split())

	return text if len(text) <= limit else text[:limit-1].rstrip() + '…'


def color(text: str, fg: str, bg: str = None) -> str:
	'''
	Color text

	:param text: Text to color
	:param fg: Foreground color code
	:param bg: Background color code
	'''

	return f'{COLOR}{fg},{bg}{text}{COLOR}' if bg else f'{COLOR}{fg}{text}{COLOR}'


def duration(seconds: int) -> str:
	'''
	Convert seconds into a H:MM:SS or M:SS string

	:param seconds: Duration in seconds
	'''

	hours, remainder = divmod(int(seconds), 3600)
	minutes, seconds = divmod(remainder, 60)

	return f'{hours}:{minutes:02}:{seconds:02}' if hours else f'{minutes}:{seconds:02}'


def line(tag: str, *fields: str, nsfw: bool = False) -> str:
	'''
	Build a single output line from a site tag and a list of fields, skipping empty fields

	:param tag: Site tag (see site_tag)
	:param fields: Fields to join with a separator
	:param nsfw: Prepend a red NSFW tag
	'''

	prefix = tag + (' ' + site_tag('NSFW', WHITE, RED) if nsfw else '')
	output = prefix + ' ' + SEP.join(field for field in fields if field)

	return truncate(output)


def number(value: int | float | str) -> str:
	'''
	Humanize a number (1234 -> 1.2K, 1234567 -> 1.2M)

	:param value: Number to humanize
	'''

	try:
		value = float(value)
	except (TypeError, ValueError):
		return str(value)

	for suffix, size in (('B', 1e9), ('M', 1e6), ('K', 1e3)):
		if abs(value) >= size:
			return f'{value / size:.1f}'.rstrip('0').rstrip('.') + suffix

	return str(int(value))


def site_tag(name: str, fg: str, bg: str) -> str:
	'''
	Build a colored site tag

	:param name: Site name
	:param fg: Foreground color code
	:param bg: Background color code
	'''

	return f'{BOLD}{COLOR}{fg},{bg} {name} {RESET}'


def size(value: int) -> str:
	'''
	Humanize a byte count

	:param value: Number of bytes
	'''

	for unit in ('B', 'KB', 'MB', 'GB'):
		if value < 1024 or unit == 'GB':
			return f'{value} {unit}' if unit == 'B' else f'{value:.1f} {unit}'
		value /= 1024


def runtime(seconds: int) -> str:
	'''
	Format a media length with a stopwatch icon

	:param seconds: Length in seconds
	'''

	return '⏱ ' + duration(seconds)


def stat(value: int | float | str, label: str) -> str:
	'''
	Format a statistic with its icon, a humanized value colored by stat type, and a grey label

	:param value: Statistic value (already humanized strings like '2.4M' are kept as-is)
	:param label: Statistic label
	'''

	icon, fg = STATS.get(label, (None, None))
	value    = color(number(value), fg) if fg else number(value)

	return (f'{icon} ' if icon else '') + f'{value} {color(label, GREY)}'


def timestamp(value: str) -> float:
	'''
	Convert an ISO 8601 date string into a unix timestamp (naive dates are treated as UTC)

	:param value: ISO 8601 date string
	'''

	date = datetime.datetime.fromisoformat(value)

	return (date if date.tzinfo else date.replace(tzinfo=datetime.UTC)).timestamp()


def truncate(text: str, limit: int = MAX_BYTES) -> str:
	'''
	Truncate text to a maximum number of UTF-8 bytes without splitting characters

	:param text: Text to truncate
	:param limit: Maximum number of bytes
	'''

	data = text.encode('utf-8')

	if len(data) <= limit:
		return text

	return data[:limit-3].decode('utf-8', 'ignore') + RESET + '…'
