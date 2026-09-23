(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const contract = JSON.parse($('orw-contract').textContent);
  const fields = {'$.project_title': 'project-title', '$.project_description': 'description', '$.creator.name': 'creator-name', '$.creator.orcid': 'orcid', '$.first_study.title': 'study-title', '$.first_assay': 'assay-title', '$.first_assay.title': 'assay-title', '$.data.location': 'data-location', '$.data.access': 'data-access', '$.keywords': 'keywords'};
  const form = $('workspace-form');
  let current = null, blobUrl = null;
  const revoke = () => { if (blobUrl) URL.revokeObjectURL(blobUrl); blobUrl = null; };
  function clearErrors() {
    $('errors').replaceChildren(); $('errors').hidden = true;
    for (const id of Object.values(fields)) $(id).removeAttribute('aria-invalid');
  }
  function invalidate() {
    current = null; revoke(); $('download').disabled = true; $('confirmation').checked = false;
    $('confirmation-row').hidden = true; $('summary').hidden = true; $('metadata-details').hidden = true;
    $('metadata').textContent = ''; $('status').hidden = true; $('next-steps').hidden = true;
    $('preview-badge').textContent = 'Review needed'; $('preview-badge').classList.remove('ready');
    $('preview-intro').textContent = 'Review your current entries before downloading. Nothing has been saved by this page.';
    $('tree').textContent = 'Complete the form and choose “Review workspace” to see the exact files.';
    $('folder-name').textContent = 'my-research-project/';
  }
  function showErrors(error) {
    clearErrors();
    const issues = error.issues || [{path: '$', message: error.message || 'Workspace generation failed.'}];
    const heading = document.createElement('p'); heading.textContent = 'Check these entries before continuing:';
    const list = document.createElement('ul');
    for (const issue of issues) {
      const id = fields[issue.path] || (issue.path.startsWith('$.keywords[') ? 'keywords' : null);
      const item = document.createElement('li');
      const text = id === 'orcid' ? 'ORCID: use 0000-0002-1825-0097 format, or leave this optional field blank.' : (id ? $(id).labels[0].textContent.trim() + ': ' : '') + issue.message;
      if (id) {
        $(id).setAttribute('aria-invalid', 'true');
        const link = document.createElement('a'); link.href = '#' + id; link.textContent = text;
        link.addEventListener('click', event => { event.preventDefault(); $(id).focus(); }); item.append(link);
      } else item.textContent = text;
      list.append(item);
    }
    $('errors').append(heading, list); $('errors').hidden = false; $('errors').focus();
  }
  function readForm() {
    const assay = $('assay-title').value;
    return {project_title: $('project-title').value, project_description: $('description').value,
      creator: {name: $('creator-name').value, orcid: $('orcid').value || null},
      first_study: {title: $('study-title').value}, first_assay: assay ? {title: assay} : null,
      data: {location: $('data-location').value, access: $('data-access').value},
      keywords: $('keywords').value.split(',').map(ORW.trim).filter(Boolean)};
  }
  function fileTree(files) {
    const tree = {};
    for (const name of Object.keys(files).sort()) {
      let node = tree; const parts = name.split('/');
      parts.forEach((p, i) => { if (!Object.prototype.hasOwnProperty.call(node, p)) node[p] = i === parts.length - 1 ? null : {}; node = node[p]; });
    }
    function walk(node, prefix) {
      const entries = Object.entries(node);
      return entries.flatMap(([name, child], i) => {
        const last = i === entries.length - 1;
        return [prefix + (last ? '└── ' : '├── ') + name + (child ? '/' : ''), ...(child ? walk(child, prefix + (last ? '    ' : '│   ')) : [])];
      });
    }
    return walk(tree, '').join('\n');
  }
  form.addEventListener('submit', event => {
    event.preventDefault(); invalidate(); clearErrors();
    try {
      current = ORW.generate(readForm(), contract);
      $('folder-name').textContent = current.folder + '/'; $('tree').textContent = fileTree(current.files);
      $('metadata').textContent = current.files['.research/project.yml']; $('metadata-details').hidden = false;
      $('file-count').textContent = String(Object.keys(current.files).length); $('access-summary').textContent = current.setup.data.access;
      $('summary').hidden = false; $('confirmation-row').hidden = false;
      $('preview-badge').textContent = 'Ready to save'; $('preview-badge').classList.add('ready');
      $('preview-intro').textContent = 'Setup and generated metadata pass the bundled ORW schemas. Review the contents below. This is not a FAIR certification.';
      $('confirmation').focus();
    } catch (error) { current = null; showErrors(error); }
  });
  form.addEventListener('input', () => { invalidate(); clearErrors(); });
  form.addEventListener('change', () => { invalidate(); clearErrors(); });
  form.addEventListener('reset', () => {
    invalidate(); clearErrors(); $('example-note').hidden = true;
    $('preview-badge').textContent = 'Not generated';
  });
  $('confirmation').addEventListener('change', () => { $('download').disabled = !current || !$('confirmation').checked; });
  $('download').addEventListener('click', () => {
    if (!current || !$('confirmation').checked) return;
    try {
      const bytes = ORW.zip(current.files, current.folder); revoke();
      blobUrl = URL.createObjectURL(new Blob([bytes], {type: 'application/zip'}));
      const link = document.createElement('a'); link.href = blobUrl; link.download = current.folder + '-workspace.zip';
      document.body.append(link); link.click(); link.remove();
      $('status').textContent = 'ZIP prepared locally. Check your browser’s downloads, then extract the folder. No project data were uploaded or published.';
      $('status').hidden = false; $('next-steps').hidden = false;
    } catch (error) { showErrors(error); }
  });
  $('example').addEventListener('click', () => {
    const hasEntries = [...form.querySelectorAll('input, textarea')].some(field => field.value);
    if (hasEntries && !window.confirm('Replace your current entries with the demonstration example?')) return;
    form.reset();
    const data = {'project-title': 'Effects of light exposure on mouse activity', description: 'Study of how altered light exposure affects spontaneous mouse activity.', 'creator-name': 'Jane Researcher', 'study-title': 'Light exposure study', 'assay-title': 'Behaviour', 'data-location': 'Institutional research server', keywords: 'behaviour, circadian rhythm, mouse'};
    for (const [id, value] of Object.entries(data)) $(id).value = value;
    $('data-access').value = 'private'; $('example-note').hidden = false; $('project-title').focus();
  });
  for (const access of contract.setupSchema.properties.data.properties.access.enum) {
    const option = document.createElement('option'); option.value = access; option.textContent = access[0].toUpperCase() + access.slice(1);
    option.defaultSelected = access === 'private'; $('data-access').append(option);
  }
  // The one place this page talks to the network, and only on a click. The
  // ORCID is sent to orcid.org and the public name read back; nothing else
  // about the workspace leaves the browser, and the form stays usable when the
  // registry is unreachable. CSP allows this origin and no other.
  const orcidShape = new RegExp(contract.setupSchema.properties.creator.properties.orcid.pattern, 'u');
  function orcidStatus(message, state) {
    const status = $('orcid-status');
    status.textContent = message;
    status.className = 'hint' + (state ? ' ' + state : '');
    status.hidden = !message;
  }
  $('orcid-lookup').addEventListener('click', async () => {
    const button = $('orcid-lookup');
    const raw = $('orcid').value.trim();
    if (!raw) { orcidStatus('Enter an ORCID first.', 'missing'); return; }
    if (!orcidShape.test(raw)) { orcidStatus('Use the 0000-0002-1825-0097 format.', 'missing'); return; }
    const id = raw.replace(/^https:\/\/orcid\.org\//, '');
    button.disabled = true; orcidStatus('Asking orcid.org…');
    try {
      const response = await fetch('https://pub.orcid.org/v3.0/' + id + '/person', {headers: {Accept: 'application/json'}});
      if (response.status === 404) { orcidStatus('No such ORCID in the registry. Check it against the researcher’s record.', 'missing'); return; }
      if (!response.ok) { orcidStatus('The registry answered with an error. Your entry is unchanged.', null); return; }
      const person = await response.json();
      const part = key => (person.name && person.name[key] && person.name[key].value || '').trim();
      const full = [part('given-names'), part('family-name')].filter(Boolean).join(' ');
      if (!full) { orcidStatus('ORCID exists. Its owner keeps the name private, so nothing was filled in.', 'found'); return; }
      // What the researcher typed wins, exactly as it does on the command line.
      if (!$('creator-name').value.trim()) {
        $('creator-name').value = full;
        orcidStatus('ORCID belongs to ' + full + ', filled in above.', 'found');
      } else {
        orcidStatus('ORCID belongs to ' + full + '. Your name entry was left as you wrote it.', 'found');
      }
      invalidate();
    } catch (_) {
      orcidStatus('Could not reach the registry. You can carry on; nothing was changed.', null);
    } finally { button.disabled = false; }
  });
  $('orcid').addEventListener('input', () => orcidStatus('', null));
  $('version').textContent = 'Core ' + contract.variants['00'].project.spec_version + ' · browser generator';
  $('review').disabled = false; $('example').disabled = false;
  window.addEventListener('pagehide', () => { revoke(); current = null; });
}());
