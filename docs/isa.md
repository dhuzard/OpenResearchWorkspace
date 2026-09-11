# ISA in OpenResearchWorkspace

OpenResearchWorkspace uses the **ISA (Investigation, Study, Assay)** model as its scientific organizational backbone.

## Why ORW adopts ISA

ORW needs a stable answer to basic questions: What is the overall project? Which experiments/studies belong to it? What subjects or samples were studied? Which factors or treatments were applied? What measurements were made? Which protocols and technologies produced which data?

Defining a new ORW-specific hierarchy would create another metadata model for researchers and software to map. ISA already addresses this problem and is used for rich descriptions of experimental metadata across life-science, environmental and biomedical research.

ISA gives ORW:

1. **A mature scientific hierarchy.** Investigation → Study → Assay separates overall project context, research design and analytical measurements.
2. **Provenance-oriented semantics.** ISA models subjects/sources, samples, processes, protocols, factors, measurements and data relationships rather than treating research as an unstructured collection of files.
3. **Interoperability.** ISA has defined ISA-Tab and ISA-JSON serializations and an existing tooling ecosystem.
4. **Ontology support.** ISA supports ontology annotations for concepts such as measurement and technology types.
5. **A FAIR/reproducibility foundation.** Structured sample-to-data and process relationships make experimental metadata more reusable and interpretable.
6. **A better basis for AI/agents.** An agent can reason more reliably about an explicit Investigation/Study/Assay graph than infer scientific roles from filenames and folders.

ORW therefore extends and operationalizes ISA in a researcher workspace; it should not compete with ISA by inventing parallel meanings for project, experiment or measurement.

## ISA concepts in ORW

### Investigation

The overall scientific project/context. In the primary GitHub implementation, the ORW repository normally represents one Investigation.

Examples of Investigation-level information:

- title and description;
- contacts/contributors;
- publications;
- related identifiers;
- the Studies belonging to the Investigation;
- project-wide documentation and references.

### Study

A unit of research within the Investigation. A Study contextualizes subjects/sources and samples, study design, factors/treatments and protocols, and groups one or more Assays.

Examples:

- a cohort;
- a controlled animal experiment;
- a treatment experiment;
- a longitudinal study;
- a distinct experimental arm that warrants its own study-level design context.

### Assay

A measurement/test performed on study material or subjects. An Assay records what is measured, the technology/method used, processing/protocol context and links to generated data.

Examples:

- behavioural tracking;
- ECG recording;
- electrophysiology;
- RNA sequencing;
- microscopy;
- mass spectrometry;
- clinical or laboratory measurement.

## ORW folder mapping

```text
ORW repository                         ISA Investigation
└── studies/<study-id>/                ISA Study
    └── assays/<assay-id>/             ISA Assay
```

Folders are the human interface. The canonical machine-readable metadata must carry the ISA relationships explicitly; software must not infer the entire scientific model only from paths.

## ORW is ISA-aligned, not ISA-hidden complexity

Adopting ISA does **not** mean asking a beginner to manually write ISA-Tab files or a large ISA-JSON document.

The intended workflow is:

```text
simple ORW forms / workspace actions
              ↓
canonical ISA-aligned ORW metadata
              ↓
      ┌───────┼────────┐
      ▼       ▼        ▼
  ISA-JSON  ISA-Tab   other FAIR/repository representations
```

The researcher enters scientific information once. Adapters generate interoperable representations.

## Canonical metadata strategy

ORW's canonical metadata should preserve ISA concepts and identifiers while also containing ORW workspace-specific information that ISA does not attempt to model, such as capability activation or agent policy. These concerns must remain separated:

```text
Scientific metadata       → ISA-aligned project model
Workspace implementation  → .research/workspace.yml
Optional capabilities     → .research/capabilities.yml
Agent/tool policy          → later capability-specific contracts
```

ORW should progressively increase formal ISA compatibility. The immediate requirement is structural/semantic alignment; later work should provide validated ISA-JSON/ISA-Tab import/export and round-trip tests.

## Important boundary

ISA is primarily an experimental metadata model. ORW is a broader working research workspace. ORW can therefore contain code, notes, environments, tasks, analyses, provenance extensions and agent configuration that are outside ISA's scope. These additions must complement ISA rather than redefine Investigation, Study or Assay.

## References

- ISA Model and Serialization Specifications: https://isa-specs.readthedocs.io/
- ISA Abstract Model: https://isa-specs.readthedocs.io/en/latest/isamodel.html
- ISA-Tab: https://isa-specs.readthedocs.io/en/latest/isatab.html
- ISA-JSON: https://isa-specs.readthedocs.io/en/latest/isajson.html
- ISA tools: https://isa-tools.org/
