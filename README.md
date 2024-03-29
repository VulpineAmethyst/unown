Unown
-----
Unown is a script for generating an EPUB 3.0 Container from a set of
files. It includes support for inclusion and exclusion lists.

Usage
-----
`unown.py config.toml`

The script outputs EPUBs based on the title specified in the config
file. For inclusion and exclusion list-based generation, it incorporates
the name of the list. For example, an inclusion list named 'story' for a
book with the title "An Example" would generate `An Example story.epub`.

Configuration
-------------
The following is a minimalistic configuration for Unown, with comments.

```toml
title="An Example"
#subtitle="..."
language="en-US"
# Not actually used, but should be the copyright year.
copyright=2018
creator="John Doe"
contributors=[ "Jane Doe" ]
# Where we should look for your files.
directory="example"
# This setting will cause Unown to generate a 'complete' package even
# if inclusion or exclusion lists are specified.
generate_all=true
# The uuid is generated by Unown and should be left intact if present,
# unless you're copying an old configuration, in which case it should
# be removed. 
#uuid = "..."

# Inclusion lists are presumed to consist only of viewable documents under
# the OEBPS subdirectory of the directory configured above. Other
# files (CSS, etc.) should be in the configured directory.
#
# Inclusion UUIDs are used in lieu of the primary UUID for inclusion-
# based EPUB generation.
#[include]
#story=[ 'foo.html', 'bar.html' ]
#story_uuid = "..."

# Exclusion lists exclude only files in the OEBPS subdirectory of the
# directory configured above. Other files in the configured directory
# are included regardless.
#[exclude]
#choice=[ 'baz.html' ]
#choice_uuid = "..."
```

Templates
---------
Unown includes a set of Jinja2 templates in the `templates/` directory.
The following is a list of templates for Unown.

* `container.xml` -- Not actually a template, but it's part of the EPUB
  3.0 Container specification, and it points to the `.opf` file.
* `nav.html` -- Used to generate the table of contents for navigation.
* `package.xml` -- Used to generate the EPUB 3.0 Package Document for
  the ebook. This file is specified in `container.xml`.

Contributions
-------------
The `contrib/` directory contains a collection of scripts which may be
of interest. See `README.md` in that directory for more information.
