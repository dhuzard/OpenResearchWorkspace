# Scientist-facing reference implementation

The first implementation of OpenResearchWorkspace should optimize for a scientist who has never used Git.

## User journey

### 1. Create project
The researcher selects **Create research project**.

They answer a short form:
- title;
- description;
- contributors;
- ORCIDs where available;
- keywords;
- where data will live;
- whether data are sensitive/restricted.

The system writes `.research/project.yml`.

### 2. Collaborate
The researcher selects **Add collaborators**.

GitHub permissions are used underneath, but the UI describes people as project collaborators.

### 3. Work
The visible project surface is:

```text
Project overview
Files
Data
Analysis
Results
Tasks
```

### 4. Publish
The researcher selects **Publish project**.

The system:
1. validates required metadata;
2. warns about secrets/restricted data;
3. shows the material that will become public;
4. requests explicit confirmation;
5. creates a version;
6. sends it to the configured archive;
7. reports the DOI/PID.

## What should remain hidden by default

- YAML;
- Git branches;
- commits;
- tags;
- Actions;
- release internals;
- generated `CITATION.cff`;
- DataCite JSON;
- RO-Crate JSON-LD.

Advanced users may access all of them.

## Critical usability metric

A new researcher should be able to create and understand a project without reading Git documentation.
