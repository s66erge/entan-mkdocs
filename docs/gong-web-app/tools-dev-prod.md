# Tools + sync code<->doc

## Tools used in dev and prod

These tools are described in the section `Setup deploy`.

- [Python](../setup-dev/a-python-environ.md): main programming language, with some JavaScript
- [Entangled](../setup-dev/entangled.md): for permanent sync of code and documentation
- [MkDocs/Material](../setup-dev/mkdocs.md): for generating the documentation static site
- [Railway](../setup-prod/railway.md): the production service


## Automatic sync code <-> documentation

[Entangled](../setup-dev/entangled.md) synchronizes automatically the code in each of the markdown files here below with one of the app python files: `\libs\*.py`, plus `\main.py`.

Read carefully the doc and ensure smooth usage with git !

In the first code block of all files in the section `Gong web app code`:

- The first line is a comment with the file path of the python file that will be synchronized with this markdown file
- The subsequent lines contain the import statements for the whole python file
- Then the identifiers between << and >> are the name of the code sections that will be synchronized with the python file, in the order they appear here (not a priori in the order the code sections are written below). These identifiers are in the first line of each of the following code sections.
