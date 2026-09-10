# Frequently asked questions

## Is ORW a web application?

No. ORW is a workspace specification/contract plus reference implementations. The primary reference implementation is a GitHub template. A lightweight UI may be added later to make setup and common actions easier, but the scientist's own repository remains the canonical workspace.

## Should researchers fork the ORW repository?

No. Normal users should create a new independent project from the GitHub template.

Forks are useful for contributing back to ORW itself. They are not the intended model for independent research projects.

## Why use GitHub if researchers should not need to learn Git?

GitHub provides repository hosting, version history, collaboration, access control, automation, and release infrastructure. ORW treats those as implementation details and aims to expose simpler researcher-facing actions such as setup, collaborate, check project, and publish.

## Does the template stay synchronized with ORW?

No. A project created from the template evolves independently.

The workspace records its ORW specification/template version. Future improvements should be introduced through explicit workspace migrations or tooling rather than asking researchers to merge upstream template history.

## Is ORW intended to store all research data?

No. Large, sensitive, regulated, or discipline-specific data may belong in institutional storage or dedicated scientific repositories. ORW should record where authoritative data live and link them through identifiers and metadata.

## Is FAIR an optional plugin?

Basic structured metadata and machine readability belong in the core design. More advanced FAIR functionality—such as DataCite export, RO-Crate, FAIR Signposting, richer PID support, and repository integrations—is layered as capabilities.

## Are reproducibility and agent-readiness separate project types?

No. They are capabilities of the same research workspace. A project can progressively enable them without being recreated from another template.

## Will ORW support AI agents?

Yes, progressively. The intended architecture is provider-neutral: first define an agent contract, then reusable skills, then thin provider-specific adapters, and finally evaluate different agents against the same workspace and benchmark.

## Is ORW tied to one AI provider?

No. Scientific context, policies, and skills should be provider-neutral. Provider-specific files should mainly help each agent discover and apply those shared rules.

## What license does ORW use?

**OpenResearchWorkspace itself is MIT licensed.** This applies to the ORW software, template infrastructure, and reusable scaffolding.

A research project created from the ORW template is a separate project. Its scientific outputs do **not** automatically inherit the MIT license; researchers should choose appropriate licenses for their own code, data, documentation, manuscripts, figures, and other outputs.

## What is the main v0 success criterion?

A scientist unfamiliar with Git should be able to create, initialize, understand, collaborate on, and eventually publish a research project without reading Git documentation.
