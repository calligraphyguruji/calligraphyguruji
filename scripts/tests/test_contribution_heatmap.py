"""Deterministic test-only counts; never used to generate the profile asset."""
from datetime import date, timedelta
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

MODULE = Path(__file__).resolve().parents[1] / 'generate_contribution_heatmap.py'
spec = importlib.util.spec_from_file_location('heatmap', MODULE)
heatmap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(heatmap)
NS = {'s': 'http://www.w3.org/2000/svg'}


def fixture(end=date(2026, 10, 23)):
    days = [{'date': str(end - timedelta(days=364-i)),
             'contributionCount': (0, 1, 12, 123)[i % 4],
             'contributionLevel': ('NONE', 'FIRST_QUARTILE', 'SECOND_QUARTILE', 'FOURTH_QUARTILE')[i % 4]}
            for i in range(365)]
    return {'totalContributions': sum(d['contributionCount'] for d in days),
            'weeks': [{'contributionDays': days[i:i+7]} for i in range(0, 365, 7)]}


class HeatmapTests(unittest.TestCase):
    def setUp(self):
        self.end = date(2026, 10, 23)
        self.start = self.end - timedelta(days=364)
        self.raw = fixture(self.end)

    def test_svg_exact_counts_positions_and_bounds(self):
        days = heatmap.select_days(self.raw, self.start, self.end)
        svg = heatmap.render_svg(days, 'test<&')
        root = ET.fromstring(svg)
        width, height = map(float, root.attrib['viewBox'].split()[2:])
        groups = root.findall('s:g', NS)
        self.assertEqual(len(groups), 365)
        self.assertIn(str(self.raw['totalContributions']), ''.join(root.itertext()).replace(',', ''))
        for group, (day, count) in zip(groups, days):
            self.assertEqual(group.attrib['data-date'], str(day))
            rect = group.find('s:rect', NS)
            label = group.find('s:text', NS)
            self.assertEqual(float(rect.attrib['y']), 96 + ((day.weekday()+1) % 7)*23)
            if count:
                self.assertEqual(label.text, str(count))
                self.assertEqual(float(label.attrib['x']), float(rect.attrib['x'])+10)
                self.assertEqual(float(label.attrib['y']), float(rect.attrib['y'])+10)
                self.assertEqual(label.attrib['class'], 'count')
                if count == 123:
                    self.assertIn('font-size:9px', label.attrib['style'])
            else:
                self.assertIsNone(label)
                self.assertEqual(rect.attrib['fill'], '#161b22')
        for rect in root.findall('.//s:rect', NS):
            x, y, w, h = (float(rect.attrib[key]) for key in ('x','y','width','height'))
            self.assertTrue(0 <= x <= x+w <= width)
            self.assertTrue(0 <= y <= y+h <= height)
        self.assertFalse(root.findall('.//s:script', NS))
        self.assertFalse(root.findall('.//s:foreignObject', NS))

    def test_boundaries_leap_year_and_all_weekday_endings(self):
        for end in [date(2024, 3, 1)] + [date(2026, 10, 18)+timedelta(days=i) for i in range(7)]:
            days = heatmap.select_days(fixture(end), end-timedelta(days=364), end)
            self.assertEqual(len(days), 365)
            ET.fromstring(heatmap.render_svg(days, 'test'))

    def test_zero_and_tied_distributions(self):
        for count in (0, 1, 999):
            days = [(self.start+timedelta(days=i), count) for i in range(365)]
            root = ET.fromstring(heatmap.render_svg(days, 'test'))
            self.assertEqual(len(root.findall('s:g/s:text', NS)), 365 if count else 0)

    def test_reject_missing_duplicate_negative_bad_level_and_total(self):
        for kind in ('missing', 'duplicate', 'negative', 'level', 'total'):
            raw = fixture()
            first = raw['weeks'][0]['contributionDays'][0]
            if kind == 'missing': raw['weeks'][0]['contributionDays'].pop(0)
            if kind == 'duplicate': raw['weeks'][0]['contributionDays'].append(first.copy())
            if kind == 'negative': first['contributionCount'] = -1
            if kind == 'level': first['contributionLevel'] = 'INVALID'
            if kind == 'total': raw['totalContributions'] += 1
            with self.subTest(kind=kind), self.assertRaises(heatmap.HeatmapError):
                heatmap.select_days(raw, self.start, self.end)

    def test_extra_boundary_dates_trimmed_without_rebucketing(self):
        self.raw['weeks'][0]['contributionDays'].insert(0, {
            'date': str(self.start-timedelta(days=1)), 'contributionCount': 5,
            'contributionLevel': 'FIRST_QUARTILE'})
        self.raw['totalContributions'] += 5
        days = heatmap.select_days(self.raw, self.start, self.end)
        self.assertEqual(sum(n for _, n in days), self.raw['totalContributions']-5)

    def test_atomic_idempotent_output_and_missing_auth(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'test.svg'
            self.assertTrue(heatmap.write_svg(path, '<svg/>'))
            stamp = path.stat().st_mtime_ns
            self.assertFalse(heatmap.write_svg(path, '<svg/>'))
            self.assertEqual(stamp, path.stat().st_mtime_ns)
            with self.assertRaises(heatmap.HeatmapError):
                heatmap.fetch_calendar('test', self.start, self.end, '')
            self.assertEqual(path.read_text(), '<svg/>')

    @unittest.skipUnless(os.environ.get('HEATMAP_TEST_ENDPOINT'), 'Optional Postman HTTP simulation')
    def test_real_http_client_against_postman(self):
        base = os.environ['HEATMAP_TEST_ENDPOINT']
        raw = heatmap.fetch_calendar('fixture-user', self.start, self.end, 'test-only', endpoint=base+'/graphql')
        self.assertEqual(len(heatmap.select_days(raw, self.start, self.end)), 365)
        for route in ('auth', 'rate', 'graphql-error', 'malformed', 'server-error', 'retry'):
            with self.subTest(route=route), patch.object(heatmap.time, 'sleep'):
                if route == 'retry':
                    self.assertEqual(heatmap.fetch_calendar('fixture-user', self.start, self.end, 'test-only', endpoint=base+'/'+route), raw)
                else:
                    with self.assertRaises(heatmap.HeatmapError):
                        heatmap.fetch_calendar('fixture-user', self.start, self.end, 'test-only', endpoint=base+'/'+route)


if __name__ == '__main__':
    unittest.main()
