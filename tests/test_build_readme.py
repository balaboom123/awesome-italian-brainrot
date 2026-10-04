"""Regression checks for metadata validation, asset links, and stale pages."""
import copy
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'build_readme.py'
spec = importlib.util.spec_from_file_location('build_readme', SCRIPT)
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / 'characters' / 'sample'
        self.folder.mkdir(parents=True)
        self.thumbnail = self.folder / 'sample_fandom.webp'
        self.thumbnail.write_bytes(b'thumbnail fixture')
        self.character = {
            'name': 'Sample', 'slug': 'sample', 'kind': 'original',
            'aliases': [], 'thumb': 'fandom', 'sources': {'fandom': {}},
        }
        patcher = patch.multiple(build, ROOT=str(self.root), CHARS=str(self.root / 'characters'))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_malformed_metadata_returns_errors(self):
        cases = [None, {}, [], [None], [1], [{}]]
        for field, value in [
            ('slug', ['invalid']), ('slug', '../escape'), ('name', None),
            ('kind', {}), ('aliases', 'alias'), ('aliases', [None]),
            ('sources', []), ('sources', {'fandom': None}), ('thumb', []),
            ('origin', {}), ('audio_source', 'https-not-a-url'),
        ]:
            c = copy.deepcopy(self.character)
            c[field] = value
            cases.append([c])
        for case in cases:
            with self.subTest(case=case):
                self.assertTrue(build.check_schema(case))

    def test_alias_collisions_and_fusion_components(self):
        other = copy.deepcopy(self.character)
        other.update(name='Other', slug='other', aliases=['SAMPLE'])
        self.assertTrue(build.check_schema([self.character, other]))
        other.update(aliases=[], kind='fusion', components=['sample', 'sample'])
        self.assertTrue(build.check_schema([self.character, other]))
        other['components'] = ['sample', 'other']
        self.assertTrue(build.check_schema([self.character, other]))
        other['components'] = ['sample', 'missing']
        self.assertTrue(build.check_schema([self.character, other]))

    def test_missing_hires_never_becomes_an_assumed_release_link(self):
        self.character['sources']['fandom']['hires'] = '900x900'
        self.assertTrue(build.check_files([self.character]))
        self.character['sources']['fandom']['hires_url'] = 'https://example.org/original.png'
        self.assertEqual(build.check_files([self.character]), [])
        page = build.char_readme(self.character)
        self.assertIn('https://example.org/original.png', page)
        self.assertNotIn('releases/latest', page)
        (self.folder / 'sample_fandom_full.png').write_bytes(b'full-size fixture')
        self.assertIn('](sample_fandom_full.png)', build.char_readme(self.character))

    def test_sources_need_assets_and_files_need_metadata(self):
        self.character['sources']['commons'] = {'url': 'https://commons.wikimedia.org/wiki/File:Sample.webp'}
        self.assertTrue(build.check_files([self.character]))
        (self.folder / 'sample_commons.webp').write_bytes(b'second source')
        self.assertEqual(build.check_files([self.character]), [])
        self.assertIn('](sample_commons.webp)', build.char_readme(self.character))
        for name in ['sample_kym.webp', 'sample_fandom.png', 'sample_fandom_full.png']:
            path = self.folder / name
            path.write_bytes(b'unlisted file')
            self.assertTrue(build.check_files([self.character]))
            path.unlink()
        (self.folder / 'unexpected').mkdir()
        self.assertTrue(build.check_files([self.character]))

    def test_media_credit_validation_and_rendering(self):
        source = self.character['sources']['fandom']
        source.update(attribution='Example <creator>', license='CC BY-SA 4.0',
                      license_url='https://creativecommons.org/licenses/by-sa/4.0/')
        self.assertEqual(build.check_schema([self.character]), [])
        page = build.char_readme(self.character)
        self.assertIn('Example &lt;creator&gt;', page)
        self.assertIn('[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)', page)
        source['attribution'] = []
        self.assertTrue(build.check_schema([self.character]))
        source['attribution'] = 'Example\rCreator'
        self.assertTrue(build.check_schema([self.character]))
        source['attribution'] = 'Example'
        source['license_url'] = 'not-a-url'
        self.assertTrue(build.check_schema([self.character]))
        source['license_url'] = 'https://example.org/license'
        self.character['audio_credit'] = {'attribution': 'Uploader', 'license': 'Unknown license'}
        self.assertTrue(build.check_schema([self.character]))
        self.character['audio_source'] = 'https://example.org/audio'
        (self.folder / 'sample.mp3').write_bytes(b'audio fixture')
        self.assertEqual(build.check_schema([self.character]), [])
        self.assertIn('Uploader · Unknown license', build.char_readme(self.character))

    def test_archived_source_label_preserves_original_page_title(self):
        self.character['thumb'] = 'miraheze'
        self.character['sources'] = {'miraheze': {
            'url': 'https://archive.org/details/wiki-example', 'page_title': 'Original page',
            'attribution': 'Wiki uploader: Example', 'license': 'Unknown media license',
        }}
        self.thumbnail.rename(self.folder / 'sample_miraheze.webp')
        self.assertEqual(build.check_schema([self.character]), [])
        self.assertEqual(build.check_files([self.character]), [])
        self.assertIn('Original page · Wiki uploader: Example · Unknown media license',
                      build.char_readme(self.character))

    def test_file_size_limits(self):
        with patch.multiple(build, MAX_THUMB=20, MAX_AUDIO=30, MAX_BYTES=40):
            self.thumbnail.write_bytes(b'x' * 20)
            self.assertEqual(build.check_files([self.character]), [])
            self.thumbnail.write_bytes(b'x' * 21)
            self.assertTrue(build.check_files([self.character]))
            self.thumbnail.write_bytes(b'x')
            audio = self.folder / 'sample.mp3'
            audio.write_bytes(b'x' * 31)
            self.assertTrue(build.check_files([self.character]))
            audio.unlink()
            self.character['sources']['fandom']['hires'] = '1x1'
            (self.folder / 'sample_fandom_full.png').write_bytes(b'x' * 41)
            self.assertTrue(build.check_files([self.character]))

    def test_command_detects_stale_pages_and_bad_json(self):
        scripts = self.root / 'scripts'
        scripts.mkdir()
        script = scripts / 'build_readme.py'
        script.write_text(SCRIPT.read_text())
        index = self.root / 'characters.json'
        index.write_text(json.dumps([self.character]))

        def run(*args):
            return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True)

        self.assertEqual(run().returncode, 0)
        self.assertEqual(run('--check').returncode, 0)
        page = self.folder / 'README.md'
        page.write_text(page.read_text() + '\nUntracked edit\n')
        result = run('--check')
        self.assertEqual(result.returncode, 1)
        self.assertIn('stale', result.stderr)
        self.assertTrue(page.read_text().endswith('Untracked edit\n'))
        self.assertEqual(run().returncode, 0)
        self.assertEqual(run('--check').returncode, 0)
        index.write_text('{broken')
        result = run('--check')
        self.assertEqual(result.returncode, 1)
        self.assertNotIn('Traceback', result.stderr)


class RepositoryTests(unittest.TestCase):
    def test_generated_local_links_resolve(self):
        chars = build.load()
        for filename, content in build.outputs(chars):
            links = re.findall(r'(?:href|src)="([^"]+)"', content)
            links += re.findall(r'\]\(([^)]+)\)', content)
            for link in links:
                parts = urlsplit(link)
                if parts.scheme or not parts.path:
                    continue
                target = Path(filename).parent / unquote(parts.path)
                with self.subTest(page=filename, target=str(target)):
                    self.assertTrue(target.exists(), f'Broken local link: {link}')


if __name__ == '__main__':
    unittest.main()
