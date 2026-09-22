"""Build a self-contained browser generator from the current ORW core and schemas.

No JavaScript package manager, network access, or browser runtime Python is needed.
The generated HTML may be served at any URL prefix or opened directly from disk.
"""
from __future__ import annotations

import argparse
import base64
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from orw.initialize import ImplementationContext, create_workspace, slug  # noqa: E402
from orw.model import SetupConfig  # noqa: E402

# Build-time sentinels, not user-facing defaults or a second project model.
TOKENS = {
    'projectTitle': 'ORW_SENTINEL_PROJECT_6D1A',
    'description': 'ORW_SENTINEL_DESCRIPTION_6D1A',
    'creator': 'ORW_SENTINEL_CREATOR_6D1A',
    'studyTitle': 'ORW_SENTINEL_STUDY_6D1A',
    'assayTitle': 'ORW_SENTINEL_ASSAY_6D1A',
    'location': 'ORW_SENTINEL_LOCATION_6D1A',
    'orcid': '0000-0002-1825-0097',
    'keywords': 'ORW_SENTINEL_KEYWORDS_6D1A',
    'access': 'unknown',
}
SUPPORTED = {
    '$schema', '$id', '$defs', '$ref', 'title', 'description', 'type',
    'required', 'properties', 'additionalProperties', 'items', 'oneOf',
    'const', 'enum', 'pattern', 'minLength', 'uniqueItems',
}


def check_schema(schema: dict) -> None:
    """Fail the build if the bounded browser schema interpreter would omit a rule."""
    unknown = set(schema) - SUPPORTED
    if unknown:
        raise ValueError(f'Unsupported browser schema keywords: {sorted(unknown)}')
    if '$ref' in schema and not schema['$ref'].startswith('#/$defs/'):
        raise ValueError('Browser schemas must use bundled local $defs references.')
    for key in ('properties', '$defs'):
        for child in schema.get(key, {}).values():
            check_schema(child)
    for child in schema.get('oneOf', []):
        check_schema(child)
    for key in ('items', 'additionalProperties'):
        if isinstance(schema.get(key), dict):
            check_schema(schema[key])


def make_contract() -> dict:
    setup = json.loads((ROOT / 'schema/setup.schema.json').read_text())
    project_schema = json.loads((ROOT / 'schema/project.schema.json').read_text())
    for schema in (setup, project_schema):
        check_schema(schema)
    tokens = dict(TOKENS)
    tokens.update({key: slug(TOKENS[src], fallback) for key, src, fallback in (
        ('projectId', 'projectTitle', 'investigation-01'),
        ('studyId', 'studyTitle', 'study-01'),
        ('assayId', 'assayTitle', 'assay-01'),
    )})
    variants = {}
    for assay in (False, True):
        for orcid in (False, True):
            payload = {
                'project_title': TOKENS['projectTitle'],
                'project_description': TOKENS['description'],
                'creator': {'name': TOKENS['creator'], 'orcid': TOKENS['orcid'] if orcid else None},
                'first_study': {'title': TOKENS['studyTitle']},
                'first_assay': {'title': TOKENS['assayTitle']} if assay else None,
                'data': {'location': TOKENS['location'], 'access': TOKENS['access']},
                'keywords': [TOKENS['keywords']],
            }
            with tempfile.TemporaryDirectory() as tmp:
                destination = Path(tmp) / 'workspace'
                create_workspace(SetupConfig.from_mapping(payload), destination,
                                 implementation=ImplementationContext(provider='browser'))
                files = {p.relative_to(destination).as_posix(): p.read_text(encoding='utf-8')
                         for p in sorted(destination.rglob('*')) if p.is_file()}
                project = yaml.safe_load(files.pop('.research/project.yml'))
                variants[f'{int(assay)}{int(orcid)}'] = {'project': project, 'files': files}
    sources = {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in (
        'src/orw/initialize.py', 'src/orw/model.py',
        'schema/setup.schema.json', 'schema/project.schema.json',
    )}
    return {'format': 1, 'tokens': tokens, 'variants': variants, 'setupSchema': setup,
            'projectSchema': project_schema, 'sourceHashes': sources}


def script_json(value: object) -> str:
    # Also safe when future template prose includes a literal HTML closing tag.
    return json.dumps(value, ensure_ascii=True, separators=(',', ':')).replace('<', '\\u003c')


def build(output: Path) -> Path:
    contract = make_contract()
    html = (ROOT / 'browser/page.html').read_text(encoding='utf-8')
    replacements = {'CONTRACT': script_json(contract)}
    replacements.update({key: (ROOT / path).read_text(encoding='utf-8') for key, path in (
        ('ENGINE', 'browser/engine.js'), ('APP', 'browser/app.js'), ('STYLE', 'browser/style.css'),
    )})
    # A single pass prevents inserted source text from becoming a second template.
    html = re.sub(r'@@(CONTRACT|ENGINE|APP|STYLE)@@', lambda m: replacements[m[1]], html)
    def integrity(body: str) -> str:
        return "'sha256-" + base64.b64encode(sha256(body.encode('utf-8')).digest()).decode() + "'"
    scripts = re.findall(r'<script(?:\s[^>]*)?>([\s\S]*?)</script>', html)
    styles = re.findall(r'<style>([\s\S]*?)</style>', html)
    csp = ("default-src 'none'; connect-src 'none'; form-action 'none'; base-uri 'none'; "
           "object-src 'none'; img-src data:; script-src " + ' '.join(map(integrity, scripts))
           + '; style-src ' + ' '.join(map(integrity, styles)))
    html = html.replace('@@CSP@@', csp)
    output.mkdir(parents=True, exist_ok=True)
    target = output / 'index.html'
    target.write_text(html, encoding='utf-8', newline='\n')
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/browser')
    args = parser.parse_args()
    print(build(args.output.resolve()))


if __name__ == '__main__':
    main()
