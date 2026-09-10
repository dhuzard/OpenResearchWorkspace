project = "OpenResearchWorkspace"
author = "OpenResearchWorkspace contributors"

extensions = [
    "myst_parser",
    "sphinx_design",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

html_theme = "furo"
html_title = "OpenResearchWorkspace"
html_theme_options = {
    "navigation_with_keys": True,
}

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "tasklist",
]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
