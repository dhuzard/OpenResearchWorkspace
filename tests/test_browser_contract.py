"""Compare the browser adapter with the existing Python generation/validation core.

No browser or network is needed here; Node runs the exact engine shipped in HTML.
"""
from __future__ import annotations

import base64
from copy import deepcopy
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

from jsonschema import Draft202012Validator
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from orw.initialize import ImplementationContext, create_workspace  # noqa: E402
from orw.model import SetupConfig, SetupValidationError  # noqa: E402
from orw.validate import validate_workspace  # noqa: E402
from scripts.build_browser import build, check_schema, make_contract  # noqa: E402

NODE = r"""
const fs = require('node:fs');
const engine = require(process.argv[1]);
const {payload, contract, operation, files, folder} = JSON.parse(fs.readFileSync(0, 'utf8'));
globalThis.fetch = () => { throw new Error('Network access is forbidden.'); };
try {
  if (operation === 'zip') {
    process.stdout.write(JSON.stringify({zip: Buffer.from(engine.zip(files, folder)).toString('base64')}));
  } else {
    const result = engine.generate(payload, contract);
    process.stdout.write(JSON.stringify({...result, zip: Buffer.from(engine.zip(result.files, result.folder)).toString('base64')}));
  }
} catch (error) {
  process.stdout.write(JSON.stringify({error: error.message, issues: error.issues || []}));
}
"""


def fixture(name='basic') -> dict:
    return json.loads((ROOT / f'tests/fixtures/setup/{name}.json').read_text(encoding='utf-8'))


@unittest.skipUnless(shutil.which('node'), 'Node.js is required for browser contract tests')
class BrowserContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = make_contract()

    def run_engine(self, payload=None, **kwargs):
        process = subprocess.run(
            ['node', '-e', NODE, str(ROOT / 'browser/engine.js')],
            input=json.dumps({'payload': payload, 'contract': self.contract, **kwargs}),
            text=True, encoding='utf-8', capture_output=True, check=True, timeout=20,
        )
        return json.loads(process.stdout)

    def assert_matches_core(self, payload):
        result = self.run_engine(payload)
        self.assertNotIn('error', result, result)
        normalized = SetupConfig.from_mapping(payload)
        self.assertEqual(result['setup'], normalized.to_mapping())
        with tempfile.TemporaryDirectory() as tmp:
            expected = Path(tmp) / 'python'
            create_workspace(normalized, expected, implementation=ImplementationContext(provider='browser'))
            expected_files = {p.relative_to(expected).as_posix(): p.read_text(encoding='utf-8')
                              for p in expected.rglob('*') if p.is_file()}
            self.assertEqual(set(result['files']), set(expected_files))
            for name, content in result['files'].items():
                if name == '.research/project.yml':
                    self.assertEqual(yaml.safe_load(content), yaml.safe_load(expected_files[name]))
                    Draft202012Validator(self.contract['projectSchema']).validate(yaml.safe_load(content))
                else:
                    self.assertEqual(content, expected_files[name], name)
            with zipfile.ZipFile(io.BytesIO(base64.b64decode(result['zip']))) as archive:
                self.assertIsNone(archive.testzip(), 'ZIP CRC mismatch')
                archive.extractall(Path(tmp) / 'extracted')
                self.assertEqual(len(archive.namelist()), len(expected_files))
                for info in archive.infolist():
                    self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
            extracted = Path(tmp) / 'extracted' / result['folder']
            report = validate_workspace(extracted)
            self.assertTrue(report.valid, report.issues)
            self.assertFalse((extracted / '.git').exists())
            self.assertFalse((extracted / '.github').exists())
        return result

    def test_all_existing_setup_fixtures(self):
        paths = list((ROOT / 'tests/fixtures/setup').glob('*.json'))
        self.assertGreaterEqual(len(paths), 7)
        for path in paths:
            with self.subTest(fixture=path.name):
                payload = json.loads(path.read_text(encoding='utf-8'))
                try:
                    SetupConfig.from_mapping(payload)
                except SetupValidationError:
                    self.assertIn('error', self.run_engine(payload))
                else:
                    self.assert_matches_core(payload)

    def test_all_access_levels_and_no_assay_orcid_combinations(self):
        for access in ('open', 'private', 'restricted', 'embargoed', 'unknown'):
            for assay in (False, True):
                for orcid in (False, True):
                    with self.subTest(access=access, assay=assay, orcid=orcid):
                        payload = fixture()
                        payload['data']['access'] = access
                        if not assay: payload['first_assay'] = None
                        if orcid: payload['creator']['orcid'] = '0000-0002-1825-0097'
                        result = self.assert_matches_core(payload)
                        self.assertEqual(result['project']['resources'][0]['access'], access)

    def test_unicode_quotes_newlines_and_sentinel_like_text(self):
        payload = fixture('unicode')
        payload['project_title'] += ' 🐭 "unknown"'
        payload['project_description'] = '</script><img src=x onerror=alert(1)>\nORW_SENTINEL_CREATOR_6D1A \\ quoted "text"'
        payload['creator']['name'] = '\u0085 Élodie Müller \u0085'
        payload['keywords'] = ['a', 'b"c', '未知', '🐭']
        payload['data']['location'] = 'D:\\research\\private\\data'
        self.assert_matches_core(payload)

    def test_unknown_fields_and_invalid_types_rejected(self):
        cases = []
        for key in ('project_title', 'project_description', 'creator', 'first_study', 'data'):
            for value in ('', '   ', [], None, 2, False):
                p = fixture(); p[key] = value; cases.append(p)
        p = fixture(); p['github_login'] = 'not-scientific-metadata'; cases.append(p)
        p = fixture(); p['creator']['extra'] = True; cases.append(p)
        p = fixture(); p['first_assay'] = {'title': '', 'extra': 'must not disappear'}; cases.append(p)
        p = fixture(); p['data']['access'] = 'public'; cases.append(p)
        p = fixture(); p['keywords'] = ['mouse', ' mouse ']; cases.append(p)
        for payload in cases:
            with self.subTest(payload=payload):
                self.assertIn('error', self.run_engine(payload))

    def test_optional_fields_normalize_like_python(self):
        for assay in ({}, {'title': ''}, {'title': None}, None):
            p = fixture(); p['first_assay'] = assay
            del p['creator']['orcid']; del p['keywords']
            self.assert_matches_core(p)

    def test_download_is_byte_deterministic(self):
        first, second = self.run_engine(fixture()), self.run_engine(fixture())
        self.assertEqual(first['zip'], second['zip'])
        self.assertEqual(first['files'], second['files'])

    def test_zip_rejects_unsafe_paths(self):
        for path in ('../escape', '/absolute', 'C:/drive', 'a\\b', 'a//b', 'a/./b', 'CON/file', 'NUL'):
            with self.subTest(path=path):
                self.assertIn('error', self.run_engine(operation='zip', files={path: 'x'}, folder='workspace'))
        self.assertIn('error', self.run_engine(operation='zip', files={'file': 'x'}, folder='../bad'))

    def test_zip_utf8_content_crc_and_filenames(self):
        result = self.run_engine(operation='zip', files={'résultats/é 🐭.txt': 'Δonnées\n'}, folder='study')
        with zipfile.ZipFile(io.BytesIO(base64.b64decode(result['zip']))) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(archive.read('study/résultats/é 🐭.txt').decode('utf-8'), 'Δonnées\n')

    def test_new_schema_rule_fails_build_instead_of_being_ignored(self):
        schema = deepcopy(self.contract['setupSchema'])
        schema['properties']['project_title']['maxLength'] = 10
        with self.assertRaisesRegex(ValueError, 'Unsupported browser schema'):
            check_schema(schema)

    def test_build_is_deterministic_and_has_no_remote_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = build(Path(tmp) / 'one').read_bytes()
            second = build(Path(tmp) / 'two').read_bytes()
            self.assertEqual(first, second)
            html = first.decode('utf-8')
            self.assertNotIn('@@CONTRACT@@', html)
            self.assertNotIn('@@CSP@@', html)
            # The ORCID lookup is the page's only permitted connection, and it
            # still loads nothing remotely: no external script, style or asset.
            connect = re.search(r'connect-src ([^;]+);', html).group(1).split()
            self.assertEqual(connect, ['https://pub.orcid.org'])
            self.assertIn("default-src 'none'", html)
            self.assertIn("form-action 'none'", html)
            self.assertNotIn("'unsafe-inline'", html)
            self.assertFalse(re.search(r'<script[^>]+src=', html))
            self.assertFalse(re.search(r'<link[^>]+href="(?!data:)', html))


if __name__ == '__main__':
    unittest.main()
