"""Browser acceptance tests. Run separately from the offline core test suite.

Default: real HTTP and file navigations using Playwright Chromium.
ORW_BROWSER_LOAD=content is a documented fallback for restricted CI containers
that disallow all navigation; file navigation is explicitly skipped in that mode.
"""
from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
import tempfile
from threading import Thread
import unittest
import zipfile

from playwright.sync_api import sync_playwright
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from scripts.build_browser import build  # noqa: E402
from orw.validate import validate_workspace  # noqa: E402


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class BrowserAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.folder = Path(cls.tmp.name)
        cls.html_path = build(cls.folder / 'institution' / 'research' / 'builder')
        cls.html = cls.html_path.read_text(encoding='utf-8')
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=cls.tmp.name))
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}/institution/research/builder/index.html'
        cls.playwright = sync_playwright().start()
        options = {'headless': True}
        if os.environ.get('ORW_CHROMIUM'):
            options['executable_path'] = os.environ['ORW_CHROMIUM']
        cls.browser = cls.playwright.chromium.launch(**options)
        cls.content_mode = os.environ.get('ORW_BROWSER_LOAD') == 'content'

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.playwright.stop()
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()
        cls.tmp.cleanup()

    def setUp(self):
        self.context = self.browser.new_context(accept_downloads=True, viewport={'width': 1440, 'height': 1000})
        self.page = self.context.new_page()
        self.requests, self.errors = [], []
        self.page.on('request', lambda request: self.requests.append((request.method, request.url)))
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        if self.content_mode:
            self.page.set_content(self.html)
        else:
            self.page.goto(self.url)
        self.bootstrap = len(self.requests)
        self.assertTrue(self.page.locator('#review').is_enabled())

    def tearDown(self):
        self.assertEqual(self.errors, [])
        self.context.close()

    def example(self):
        self.page.locator('#example').click()

    def review(self):
        self.page.locator('#review').click()
        self.assertTrue(self.page.locator('#errors').is_hidden())
        self.assertEqual(self.page.locator('#preview-badge').inner_text(), 'Ready to save')

    def download(self):
        self.page.locator('#confirmation').check()
        with self.page.expect_download() as event:
            self.page.locator('#download').click()
        path = self.folder / event.value.suggested_filename
        event.value.save_as(path)
        with zipfile.ZipFile(path) as archive:
            self.assertIsNone(archive.testzip())
            destination = Path(tempfile.mkdtemp(dir=self.folder))
            archive.extractall(destination)
        workspace = next(destination.iterdir())
        report = validate_workspace(workspace)
        self.assertTrue(report.valid, report.issues)
        return workspace, path

    def test_blank_form_is_not_downloadable(self):
        self.assertTrue(self.page.locator('#download').is_disabled())
        self.page.locator('#review').click()
        self.assertTrue(self.page.locator('#errors').is_visible())
        self.assertEqual(self.page.locator('#project-title').get_attribute('aria-invalid'), 'true')
        self.assertEqual(self.page.evaluate('document.activeElement.id'), 'errors')
        self.assertTrue(self.page.locator('#download').is_disabled())

    def test_real_zip_download_preserves_metadata(self):
        self.example(); self.review()
        self.assertTrue(self.page.locator('#download').is_disabled(), 'Review confirmation must be explicit')
        workspace, _ = self.download()
        project = yaml.safe_load((workspace / '.research/project.yml').read_text(encoding='utf-8'))
        self.assertEqual(project['investigation']['title'], 'Effects of light exposure on mouse activity')
        self.assertEqual(project['resources'][0]['access'], 'private')
        self.assertFalse((workspace / '.github').exists())
        self.assertTrue(self.page.locator('#next-steps').is_visible())

    def test_invalid_orcid_and_duplicate_keywords(self):
        self.example(); self.page.locator('#orcid').fill('invalid'); self.page.locator('#review').click()
        self.assertEqual(self.page.locator('#orcid').get_attribute('aria-invalid'), 'true')
        self.page.locator('#orcid').fill('')
        self.page.locator('#keywords').fill('mouse, mouse'); self.page.locator('#review').click()
        self.assertTrue(self.page.locator('#errors').is_visible())
        self.assertTrue(self.page.locator('#download').is_disabled())

    def test_edits_invalidate_review_and_download(self):
        self.example(); self.review(); self.page.locator('#confirmation').check()
        self.assertTrue(self.page.locator('#download').is_enabled())
        self.page.locator('#data-access').select_option('restricted')
        self.assertTrue(self.page.locator('#download').is_disabled())
        self.assertFalse(self.page.locator('#confirmation').is_checked())
        self.review(); workspace, _ = self.download()
        project = yaml.safe_load((workspace / '.research/project.yml').read_text(encoding='utf-8'))
        self.assertEqual(project['resources'][0]['access'], 'restricted')

    def test_no_assay_unicode_and_markup_are_preserved_as_text(self):
        self.example()
        payload = '</script><img src="https://example.invalid/no-upload" onerror="alert(1)"> Élodie 🐭'
        self.page.locator('#description').fill(payload)
        self.page.locator('#project-title').fill('Étude du comportement')
        self.page.locator('#assay-title').fill('')
        self.review()
        self.assertEqual(self.page.locator('img').count(), 0)
        workspace, _ = self.download()
        project = yaml.safe_load((workspace / '.research/project.yml').read_text(encoding='utf-8'))
        self.assertEqual(project['investigation']['description'], payload)
        self.assertEqual(project['studies'][0]['assays'], [])
        self.assertEqual(self.requests[self.bootstrap:], [])

    def test_form_and_download_work_offline_without_requests(self):
        """Describing, reviewing and downloading still touch nothing.

        The ORCID lookup is the page's only connection and it needs a click, so
        the whole ordinary path must remain exactly as silent as it always was.
        """
        self.context.set_offline(True)
        self.example(); self.review(); self.download()
        self.assertEqual(self.requests[self.bootstrap:], [])
        self.assertEqual(self.context.cookies(), [])
        if not self.content_mode:
            self.assertEqual(self.page.evaluate('localStorage.length + sessionStorage.length'), 0)

    def test_typing_an_orcid_does_not_look_it_up(self):
        """Only the button connects. Typing must never phone home on its own."""
        self.example()
        self.page.locator('#orcid').fill('0000-0002-1825-0097')
        self.page.locator('#orcid').blur()
        self.review()
        self.assertEqual(self.requests[self.bootstrap:], [])

    def test_csp_allows_only_the_orcid_registry(self):
        """The lookup opened exactly one door, not the building."""
        blocked = self.page.evaluate("""async () => {
          try { await fetch('https://example.invalid/must-not-connect'); return false; }
          catch (_) { return true; }
        }""")
        self.assertTrue(blocked)
        csp = self.page.locator('meta[http-equiv="Content-Security-Policy"]').get_attribute('content')
        self.assertIn('connect-src https://pub.orcid.org', csp)
        self.assertNotIn("connect-src 'none'", csp)
        self.assertIn("default-src 'none'", csp)
        self.assertIn("form-action 'none'", csp)
        self.assertNotIn("'unsafe-inline'", csp)

    def test_clear_form_removes_preview_and_resets_private_access(self):
        self.example(); self.page.locator('#data-access').select_option('open'); self.review()
        self.page.locator('#clear').click()
        self.assertEqual(self.page.locator('#project-title').input_value(), '')
        self.assertEqual(self.page.locator('#data-access').input_value(), 'private')
        self.assertEqual(self.page.locator('#metadata').text_content(), '')
        self.assertTrue(self.page.locator('#download').is_disabled())

    def test_keyboard_submission_and_responsive_layout(self):
        self.example(); self.page.locator('#project-title').focus(); self.page.keyboard.press('Enter')
        self.assertEqual(self.page.evaluate('document.activeElement.id'), 'confirmation')
        self.page.keyboard.press('Space')
        self.assertTrue(self.page.locator('#download').is_enabled())
        for width in (1440, 768, 390):
            self.page.set_viewport_size({'width': width, 'height': 900})
            self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)
        screenshots = os.environ.get('ORW_SCREENSHOT_DIR')
        if screenshots:
            path = Path(screenshots); path.mkdir(parents=True, exist_ok=True)
            self.page.screenshot(path=str(path / 'browser-mobile.png'), full_page=True)
            self.page.set_viewport_size({'width': 1440, 'height': 1100})
            self.page.screenshot(path=str(path / 'browser-desktop.png'), full_page=True)

    # The registry is stubbed in every test below. Reaching the real pub.orcid.org
    # would make this suite depend on a third party being up, and would announce
    # each CI run to it.
    ORCID = 'https://pub.orcid.org/v3.0/0000-0002-1825-0097/person'

    def stub_registry(self, *, status=200, given='Josiah', family='Carberry', fail=False):
        def handler(route):
            if fail:
                route.abort('failed'); return
            def part(value):
                return None if value is None else {'value': value}
            body = {'name': None} if given is None and family is None else {
                'name': {'given-names': part(given), 'family-name': part(family)}}
            route.fulfill(status=status, content_type='application/json', body=json.dumps(body))
        self.page.route('https://pub.orcid.org/**', handler)

    def look_up(self, orcid='0000-0002-1825-0097'):
        self.page.locator('#orcid').fill(orcid)
        self.page.locator('#orcid-lookup').click()
        self.page.locator('#orcid-status').wait_for(state='visible')
        self.page.wait_for_function(
            "() => !document.getElementById('orcid-status').textContent.includes('Asking')")
        return self.page.locator('#orcid-status').text_content()

    def registry_calls(self):
        return [url for _method, url in self.requests[self.bootstrap:] if 'orcid.org' in url]

    def test_lookup_fills_an_empty_name_and_calls_the_registry_once(self):
        self.stub_registry()
        self.example()
        self.page.locator('#creator-name').fill('')
        message = self.look_up()
        self.assertIn('Josiah Carberry', message)
        self.assertEqual(self.page.locator('#creator-name').input_value(), 'Josiah Carberry')
        self.assertEqual(self.registry_calls(), [self.ORCID])

    def test_lookup_never_overwrites_a_name_already_typed(self):
        """What the researcher wrote wins, exactly as it does on the CLI."""
        self.stub_registry()
        self.example()
        message = self.look_up()
        self.assertIn('Josiah Carberry', message)
        self.assertEqual(self.page.locator('#creator-name').input_value(), 'Jane Researcher')

    def test_unknown_orcid_is_reported_and_fills_nothing(self):
        self.stub_registry(status=404)
        self.example()
        self.page.locator('#creator-name').fill('')
        self.assertIn('No such ORCID', self.look_up())
        self.assertEqual(self.page.locator('#creator-name').input_value(), '')

    def test_a_private_name_still_confirms_the_orcid(self):
        self.stub_registry(given=None, family=None)
        self.example()
        self.page.locator('#creator-name').fill('')
        message = self.look_up()
        self.assertIn('private', message)
        self.assertEqual(self.page.locator('#creator-name').input_value(), '')

    def test_an_unreachable_registry_leaves_the_form_usable(self):
        """The degradation promise: no network, no lookup, no loss of work."""
        self.stub_registry(fail=True)
        self.example()
        self.assertIn('Could not reach', self.look_up())
        self.review(); workspace, _ = self.download()
        self.assertTrue((workspace / '.research/project.yml').exists())

    def test_a_malformed_orcid_is_caught_before_any_request(self):
        self.stub_registry()
        self.example()
        self.assertIn('format', self.look_up('not-an-orcid'))
        self.assertEqual(self.registry_calls(), [])

    def test_lookup_does_not_survive_into_the_download(self):
        """A looked-up name is an ordinary entry; nothing extra is recorded."""
        self.stub_registry()
        self.example()
        self.page.locator('#creator-name').fill('')
        self.look_up()
        self.review()
        workspace, _ = self.download()
        project = yaml.safe_load((workspace / '.research/project.yml').read_text(encoding='utf-8'))
        contributor = project['contributors'][0]
        self.assertEqual(contributor['name'], 'Josiah Carberry')
        self.assertEqual(contributor['orcid'], '0000-0002-1825-0097')
        self.assertEqual(set(contributor) - {'name', 'role', 'orcid'}, set())

    def test_saved_html_can_be_opened_offline(self):
        if self.content_mode:
            self.skipTest('This host blocks navigation; set_content UI tests do not certify file:// navigation.')
        self.context.set_offline(True)
        self.page.goto(self.html_path.as_uri())
        self.example(); self.review(); self.download()


if __name__ == '__main__':
    unittest.main()
