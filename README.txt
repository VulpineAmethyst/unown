Requirements
------------

* Python 3.7, from https://python.org
* Run the following: pip install tomlkit lxml jinja2 bs4
  (You may need to be in a specific directory for this; if pip.exe isn't in
  your %PATH%, it's somewhere in the Python 3.7 install tree.)

Steps to use
------------
1. unown_a.py thread.html output_dir
2. Edit or remove whatever you want in output_dir/OEBPS
3. Copy and modify mhq.toml as required.
3a. Delete the uuid line for each new book.
4. unown_epub.py file.toml output.epub

