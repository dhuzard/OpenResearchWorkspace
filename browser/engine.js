/* Provider-neutral browser adapter. Templates and schemas come from the Python
 * core at build time; no metadata model or README templates are duplicated here. */
(function (root) {
  'use strict';
  const own = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
  const object = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);
  const clone = (v) => JSON.parse(JSON.stringify(v));
  const whitespace = '[\\u0009-\\u000d\\u001c-\\u0020\\u0085\\u00a0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000]';
  const trim = (v) => typeof v === 'string' ? v.replace(new RegExp('^' + whitespace + '+|' + whitespace + '+$', 'g'), '') : v;
  const slug = (v, fallback) => trim(v.toLowerCase()).replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60) || fallback;
  class InputError extends Error {
    constructor(issues) { super(issues.map(i => i.path + ': ' + i.message).join('; ')); this.issues = issues; }
  }

  /* Deliberately bounded interpreter for the keywords used by ORW's bundled
   * schemas. build_browser.py rejects unsupported keywords: never silently skip
   * a new rule. This is not a general-purpose JSON Schema implementation. */
  function validate(value, schema, base = schema, path = '$', issues = []) {
    const fail = (message) => issues.push({path, message});
    if (schema.$ref) {
      const parts = schema.$ref.slice(2).split('/').map(p => p.replace(/~1/g, '/').replace(/~0/g, '~'));
      const referenced = parts.reduce((v, p) => v && own(v, p) ? v[p] : undefined, base);
      if (!referenced) throw new Error('Unresolved bundled schema reference: ' + schema.$ref);
      validate(value, referenced, base, path, issues);
    }
    const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b);
    if (own(schema, 'const') && !equal(value, schema.const)) fail('Unexpected value.');
    if (schema.enum && !schema.enum.some(v => equal(value, v))) fail('Choose one of: ' + schema.enum.join(', ') + '.');
    if (schema.oneOf && schema.oneOf.filter(s => validate(value, s, base, path, []).length === 0).length !== 1) {
      fail('Must match exactly one allowed form.');
    }
    const type = value === null ? 'null' : Array.isArray(value) ? 'array' : typeof value;
    if (schema.type && !(Array.isArray(schema.type) ? schema.type : [schema.type]).includes(type)) {
      fail('Expected ' + [].concat(schema.type).join(' or ') + '.'); return issues;
    }
    if (typeof value === 'string') {
      if (own(schema, 'minLength') && Array.from(value).length < schema.minLength) fail('A value is required.');
      if (schema.pattern && !new RegExp(schema.pattern, 'u').test(value)) fail('Invalid format.');
    }
    if (object(value)) {
      for (const key of schema.required || []) if (!own(value, key)) issues.push({path: path + '.' + key, message: 'A value is required.'});
      for (const [key, v] of Object.entries(value)) {
        if (own(schema.properties || {}, key)) validate(v, schema.properties[key], base, path + '.' + key, issues);
        else if (schema.additionalProperties === false) issues.push({path: path + '.' + key, message: 'Unexpected field.'});
        else if (object(schema.additionalProperties)) validate(v, schema.additionalProperties, base, path + '.' + key, issues);
      }
    }
    if (Array.isArray(value)) {
      value.forEach((v, i) => { if (schema.items) validate(v, schema.items, base, path + '[' + i + ']', issues); });
      if (schema.uniqueItems && new Set(value.map(v => JSON.stringify(v))).size !== value.length) fail('Duplicate values are not allowed.');
    }
    return issues;
  }

  function normalize(input, contract) {
    if (!object(input)) throw new InputError([{path: '$', message: 'Setup must be an object.'}]);
    const p = clone(input);
    for (const key of ['project_title', 'project_description']) if (own(p, key)) p[key] = trim(p[key]);
    for (const [key, fields] of [['creator', ['name', 'orcid']], ['first_study', ['title']], ['first_assay', ['title']], ['data', ['location', 'access']]]) {
      if (object(p[key])) for (const field of fields) if (own(p[key], field)) p[key][field] = trim(p[key][field]);
    }
    if (object(p.creator) && (!own(p.creator, 'orcid') || p.creator.orcid === '')) p.creator.orcid = null;
    if (!own(p, 'first_assay')) p.first_assay = null;
    // Match SetupConfig's optional empty assay normalization without losing
    // unknown fields that the schema needs to reject.
    if (object(p.first_assay) && Object.keys(p.first_assay).every(k => k === 'title') && !p.first_assay.title) {
      if (p.first_assay.title == null || p.first_assay.title === '') p.first_assay = null;
    }
    if (!own(p, 'keywords')) p.keywords = [];
    if (Array.isArray(p.keywords)) p.keywords = p.keywords.map(trim);
    const issues = validate(p, contract.setupSchema);
    if (issues.length) throw new InputError(issues);
    return p;
  }

  function safePath(path) {
    if (typeof path !== 'string' || !path || /[\\:\x00-\x1f]/.test(path) || path.startsWith('/') || path.split('/').some(p => !p || p === '.' || p === '..')) {
      throw new Error('Unsafe archive path: ' + path);
    }
    if (path.split('/').some(p => /^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(p) || /[. ]$/.test(p))) {
      throw new InputError([{path: '$.first_study.title', message: 'A generated folder name is reserved on Windows. Use a more descriptive project, study, or measurement title.'}]);
    }
    return path;
  }

  function generate(input, contract) {
    const p = normalize(input, contract);
    const values = {
      projectTitle: p.project_title, description: p.project_description,
      creator: p.creator.name, studyTitle: p.first_study.title,
      assayTitle: p.first_assay ? p.first_assay.title : '',
      orcid: p.creator.orcid, location: p.data.location, access: p.data.access,
      keywords: p.keywords, projectId: slug(p.project_title, 'investigation-01'),
      studyId: slug(p.first_study.title, 'study-01'),
      assayId: p.first_assay ? slug(p.first_assay.title, 'assay-01') : null,
    };
    for (const [key, path] of [['projectId', '$.project_title'], ['studyId', '$.first_study.title'], ['assayId', '$.first_assay.title']]) {
      if (values[key]) {
        try { safePath(values[key]); }
        catch (error) { if (error.issues) error.issues[0].path = path; throw error; }
      }
    }
    const replacements = new Map(Object.entries(contract.tokens).filter(([k]) => k !== 'keywords').map(([k, v]) => [v, values[k]]));
    const escape = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const expression = new RegExp([...replacements.keys()].sort((a, b) => b.length - a.length).map(escape).join('|'), 'g');
    // Replace only original template tokens; inserted user strings are never
    // evaluated, interpreted as HTML, or searched again for placeholders.
    const text = (s) => s.replace(expression, token => replacements.get(token));
    function render(v) {
      if (Array.isArray(v)) return v.length === 1 && v[0] === contract.tokens.keywords ? p.keywords.slice() : v.map(render);
      if (object(v)) return Object.fromEntries(Object.entries(v).map(([k, child]) => [k, render(child)]));
      return typeof v === 'string' ? text(v) : v;
    }
    const variant = contract.variants[Number(!!p.first_assay) + '' + Number(!!p.creator.orcid)];
    if (!variant) throw new Error('Unsupported browser contract version. Rebuild the generator.');
    const project = render(variant.project);
    const issues = validate(project, contract.projectSchema);
    if (issues.length) throw new InputError(issues);
    const files = Object.fromEntries(Object.entries(variant.files).map(([path, content]) => [safePath(text(path)), text(content)]));
    // JSON is a YAML-compatible serialization; use native escaping instead of
    // maintaining a second YAML serializer or hand-concatenating metadata.
    files['.research/project.yml'] = JSON.stringify(project, null, 2) + '\n';
    const folder = safePath(values.projectId);
    return {folder, files, project, setup: p};
  }

  // Small store-only ZIP writer for generated UTF-8 text, NOT an archive reader.
  // Fixed DOS timestamps make repeat downloads byte-deterministic. Format:
  // PKWARE APPNOTE 4.3.7, 4.3.12, 4.3.16; CRC-32 and UTF-8 flag (bit 11).
  const crcTable = Uint32Array.from({length: 256}, (_, n) => {
    for (let k = 0; k < 8; k++) n = n & 1 ? 0xedb88320 ^ (n >>> 1) : n >>> 1;
    return n >>> 0;
  });
  const crc32 = (bytes) => { let c = 0xffffffff; for (const b of bytes) c = crcTable[(c ^ b) & 255] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
  function zip(files, folder) {
    safePath(folder);
    const encoder = new TextEncoder(), entries = [], parts = [], central = [];
    let offset = 0, centralSize = 0;
    const names = Object.keys(files).sort();
    if (names.length > 65535) throw new Error('Too many generated files for ZIP32.');
    for (const path of names) {
      const name = encoder.encode(safePath(folder + '/' + path));
      if (name.length > 65535 || typeof files[path] !== 'string') throw new Error('Invalid generated file.');
      const data = encoder.encode(files[path]);
      if (offset + data.length + name.length + 30 > 16 * 1024 * 1024) throw new Error('Generated workspace exceeds the 16 MiB browser limit.');
      const checksum = crc32(data), header = new Uint8Array(30), h = new DataView(header.buffer);
      h.setUint32(0, 0x04034b50, true); h.setUint16(4, 20, true); h.setUint16(6, 0x0800, true);
      h.setUint16(12, 33, true); h.setUint32(14, checksum, true); h.setUint32(18, data.length, true);
      h.setUint32(22, data.length, true); h.setUint16(26, name.length, true);
      parts.push(header, name, data); entries.push({name, size: data.length, checksum, offset});
      offset += 30 + name.length + data.length;
    }
    for (const e of entries) {
      const header = new Uint8Array(46), h = new DataView(header.buffer);
      h.setUint32(0, 0x02014b50, true); h.setUint16(4, 20, true); h.setUint16(6, 20, true);
      h.setUint16(8, 0x0800, true); h.setUint16(14, 33, true); h.setUint32(16, e.checksum, true);
      h.setUint32(20, e.size, true); h.setUint32(24, e.size, true); h.setUint16(28, e.name.length, true);
      h.setUint32(42, e.offset, true); central.push(header, e.name); centralSize += 46 + e.name.length;
    }
    const end = new Uint8Array(22), h = new DataView(end.buffer);
    h.setUint32(0, 0x06054b50, true); h.setUint16(8, entries.length, true); h.setUint16(10, entries.length, true);
    h.setUint32(12, centralSize, true); h.setUint32(16, offset, true);
    const all = [...parts, ...central, end], result = new Uint8Array(offset + centralSize + 22);
    let pos = 0; for (const part of all) { result.set(part, pos); pos += part.length; }
    return result;
  }
  const api = {generate, normalize, validate, zip, safePath, slug, trim, InputError};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.ORW = api;
}(typeof globalThis !== 'undefined' ? globalThis : this));
