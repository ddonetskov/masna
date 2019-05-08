This is a LaTeX template inspired by [the Russian PhD LaTeX template](https://github.com/AndreyAkinshin/Russian-Phd-LaTeX-Dissertation-Template).

Please note:
- the tabu package is included into the template, it's maintenance status is uncertain but the package is still so attractive, read more at the link https://github.com/tabu-fixed/tabu.

An example of workflow:
1. Zotero with Better BibTeX for managing the bibliography, try to fetch citations by their DOI links if available (Zotero can do that), it may be useful later to have all citations with links so as your reader could follow the links to read cited sources.
2. TeXstudio as a TeX editor. I suggest using lualatex as it supports Unicode and allows executing Lua code in your document, though it is slower than pdflatex.
3. Ideally, use git to track changes to your document.

Tips:
- Google Scholar is great for searching for articles but bad at citing them, I suggest using publishers' sites for those, or https://www.crossref.org/ which creates (?) DOI links and allows looking them up by title, author etc.
- TeXstudio has a handy macros % TODO to make a note of something to work later on it.