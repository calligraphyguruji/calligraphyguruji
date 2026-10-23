#!/usr/bin/env python3
"""Fetch GitHub's contribution calendar and atomically render a numbered SVG."""
import argparse
import calendar
from datetime import date, datetime, timedelta, timezone
from html import escape
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import time
import urllib.error
import urllib.request

QUERY = """query ContributionHeatmap($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}"""
COLORS = ('#161b22', '#0e4429', '#006d32', '#26a641', '#39d353')
LEVELS = ('NONE', 'FIRST_QUARTILE', 'SECOND_QUARTILE', 'THIRD_QUARTILE', 'FOURTH_QUARTILE')
OUTPUT = Path(__file__).resolve().parents[1] / 'assets/github-contribution-heatmap.svg'


class HeatmapError(Exception):
    """Safe diagnostic: never include raw responses, request headers or tokens."""


def fetch_calendar(username, start, end, token, *, endpoint='https://api.github.com/graphql'):
    if not token:
        raise HeatmapError('Set GITHUB_TOKEN (or GH_TOKEN); GraphQL requires authentication.')
    now = datetime.now(timezone.utc)
    until = min(datetime.combine(end, datetime.max.time(), timezone.utc), now)
    body = json.dumps({'query': QUERY, 'variables': {
        'login': username, 'from': f'{start}T00:00:00Z',
        'to': until.isoformat().replace('+00:00', 'Z')}}).encode()
    request = urllib.request.Request(endpoint, data=body, headers={
        'Authorization': f'Bearer {token}', 'Content-Type': 'application/json',
        'User-Agent': 'profile-contribution-heatmap', 'Accept': 'application/json'})
    for attempt in range(4):
        wait = 2 ** attempt
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)
            errors = payload.get('errors')
            if errors:
                if any(e.get('type') == 'RATE_LIMITED' for e in errors):
                    raise HeatmapError('GitHub GraphQL rate limit reached; retry on the next run.')
                raise HeatmapError('GitHub GraphQL rejected the query; check token permissions and username.')
            return payload['data']['user']['contributionsCollection']['contributionCalendar']
        except urllib.error.HTTPError as exc:
            limited = exc.code == 429 or (exc.code == 403 and (
                exc.headers.get('X-RateLimit-Remaining') == '0' or exc.headers.get('Retry-After')))
            if exc.code in (401, 403) and not limited:
                raise HeatmapError(f'GitHub authentication/permission error (HTTP {exc.code}).') from None
            if not (limited or exc.code >= 500):
                raise HeatmapError(f'GitHub request failed (HTTP {exc.code}).') from None
            try:
                wait = max(wait, float(exc.headers.get('Retry-After', 0)),
                           float(exc.headers.get('X-RateLimit-Reset', 0)) - time.time())
            except (TypeError, ValueError):
                pass
            if wait > 60 or attempt == 3:
                raise HeatmapError('GitHub unavailable or rate limited; keeping the previous SVG.') from None
        except (urllib.error.URLError, TimeoutError):
            if attempt == 3:
                raise HeatmapError('GitHub connection failed; keeping the previous SVG.') from None
        except (AttributeError, KeyError, TypeError, ValueError):
            raise HeatmapError('GitHub returned an invalid calendar response.') from None
        time.sleep(wait)
    raise HeatmapError('GitHub retries exhausted.')


def select_days(raw, start, end):
    """Reject incomplete/inconsistent data rather than silently inventing zero days."""
    try:
        days = {}
        for week in raw['weeks']:
            for item in week['contributionDays']:
                day = date.fromisoformat(item['date'])
                count = item['contributionCount']
                if day in days or type(count) is not int or count < 0 or item['contributionLevel'] not in LEVELS:
                    raise ValueError('Invalid or duplicate contribution day')
                days[day] = count
        total = raw['totalContributions']
        if type(total) is not int or sum(days.values()) != total:
            raise ValueError('Calendar total differs from the daily sum')
        wanted = [start + timedelta(days=i) for i in range((end - start).days + 1)]
        if len(wanted) != 365 or any(day not in days for day in wanted):
            raise ValueError('Expected exactly 365 complete calendar dates')
        return [(day, days[day]) for day in wanted]
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise HeatmapError(f'Invalid contribution calendar: {exc}') from None


def render_svg(days, username, *, source='GitHub GraphQL contributionCalendar'):
    start, end = days[0][0], days[-1][0]
    origin = start - timedelta(days=(start.weekday() + 1) % 7)
    columns = (end - origin).days // 7 + 1
    cell, pitch, left, top = 20, 23, 51, 96
    width, height = left + columns * pitch + 17, 326
    positive = sorted(count for _, count in days if count)
    thresholds = [positive[max(0, math.ceil(len(positive) * q / 4) - 1)] for q in (1, 2, 3)] if positive else [0, 0, 0]
    total = sum(count for _, count in days)
    def text(x, y, value, **attrs):
        extra = ''.join(f' {k.rstrip("_").replace("_", "-")}="{escape(str(v), quote=True)}"' for k, v in attrs.items())
        return f'<text x="{x}" y="{y}"{extra}>{escape(str(value))}</text>'
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
        f'<title id="title">{escape(username)} GitHub Contribution Heatmap</title>',
        f'<desc id="description">{total:,} contributions from {start} to {end}. Sunday at top, weeks left to right. Numbers are exact daily counts. Source: {escape(source)}.</desc>',
        '<style>text{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif;fill:#919ba7;font-size:12px}.count{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-weight:600;text-anchor:middle;dominant-baseline:central}</style>',
        f'<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="10" fill="#0d1117" stroke="#30363d"/>',
        text(22, 31, f'{total:,} contributions', style='font-size:20px;font-weight:600;fill:#f0f6fc'),
        text(22, 53, f'{start:%d %b %Y} – {end:%d %b %Y} · 365 days · @{username}'),
        text(width-22, 31, 'GITHUB / DAILY ACTIVITY', text_anchor='end', style='font-size:11px;letter-spacing:1px')]
    # Group month starts by week. Suppress a label only when it would collide.
    last_label = -100
    for day, _ in days:
        if day == start or day.day == 1:
            # Reserve room for the first complete month after a short partial month.
            if day == start and day.day != 1 and calendar.monthrange(day.year, day.month)[1] - day.day < 14:
                continue
            x = left + ((day - origin).days // 7) * pitch
            if x - last_label >= 38:
                parts.append(text(x, 82, calendar.month_abbr[day.month]))
                last_label = x
    for row, label in enumerate(('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat')):
        parts.append(text(18, top + row * pitch + 14, label, style='font-size:10px'))
    for day, count in days:
        offset = (day - origin).days
        x, y = left + offset // 7 * pitch, top + offset % 7 * pitch
        level = 0 if not count else 1 + sum(count > threshold for threshold in thresholds)
        parts.append(f'<g data-date="{day}" data-count="{count}"><title>{day}: {count}</title><rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{COLORS[level]}"/>')
        if count:
            size = min(12, 27 / len(str(count)))
            color = '#ffffff' if level <= 2 else '#0d1117'
            parts.append(text(x + cell / 2, y + cell / 2, count, class_='count',
                              style=f'font-size:{size:g}px;fill:{color}'))
        parts.append('</g>')
    parts.append(text(22, 292, 'Exact daily counts · GitHub calendar dates · Today may still change'))
    legend_x = width - 210
    parts.append(text(legend_x - 36, 291, 'Less'))
    for i, color in enumerate(COLORS):
        parts.append(f'<rect x="{legend_x + i * 24}" y="277" width="20" height="20" rx="3" fill="{color}"/>')
    parts.append(text(legend_x + 127, 291, 'More'))
    parts.append('</svg>')
    return '\n'.join(parts) + '\n'


def write_svg(path, svg):
    path = Path(path)
    if path.exists() and path.read_text(encoding='utf-8') == svg:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as file:
            temporary = Path(file.name)
            file.write(svg)
        temporary.replace(path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--username', default='calligraphyguruji')
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=364)
    try:
        raw = fetch_calendar(args.username, start, end, os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN'))
        days = select_days(raw, start, end)
        changed = write_svg(args.output, render_svg(days, args.username))
        print(f'{"Updated" if changed else "Unchanged"}: {len(days)} days, {sum(n for _, n in days)} contributions ({start} to {end}).')
        return 0
    except (HeatmapError, OSError) as exc:
        print(f'Heatmap update failed: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
