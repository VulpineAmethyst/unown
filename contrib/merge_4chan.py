#!/usr/bin/env python3
#
# merge_4chan.py merges posts extracted by extract_4chan.py in to a
# single document.
# Copyright (C) 2018-2022 Síle Ekaterin Liszka
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program. If not, see
# <https://www.gnu.org/licenses/>.

import os
import os.path as op

from xml.etree import ElementTree as ET
from dataclasses import dataclass, field
from typing import List

import jinja2

from lxml.etree import parse

env = jinja2.Environment(loader=jinja2.PackageLoader('unown', 'templates'))

@dataclass
class Post:
    id: str
    author: str
    date: str
    content: str
    attach: str = None

@dataclass
class Thread:
    title: str
    content: str
    posts: List[Post] = field(default_factory=list)

    def to_html(self):
        return env.get_template('thread.html').render(thread=self)

def find_files(path):
    files = []

    with os.scandir(path) as d:
        for file in d:
            name, ext = op.splitext(file.name)
            try:
                int(name)
            except ValueError:
                continue
            files.append(op.join(path, file.name))

    return files

def read_files(files):
    posts = []

    for file in files:
        html = parse(file)

        id      = html.xpath('//span[@id="post_id"]/text()')[0]
        author  = html.xpath('//span[@id="author"]/text()')[0]
        date    = html.xpath('//span[@id="date"]/text()')[0]
        comment = ET.tostring(html.xpath('//article/blockquote')[0]).decode('UTF-8')
        attach  = html.xpath('//img/@src')
        attach  = attach[0] if len(attach) else None
        posts.append(Post(id, author, date, comment, attach))

    return posts

def make_thread(path, posts):
    if path.endswith('/'):
        path = path[:-1]

    thread = {
        'posts': posts,
    }

    with open(path + '.html', 'r') as f:
        thread['title']   = f.readline()
        thread['content'] = f.read()

    with open(path + '_thread.html', 'w') as f:
        f.write(env.get_template('thread.html').render(thread=thread))

if __name__ == '__main__':
    import sys

    path = sys.argv[1]

    files = find_files(path)
    posts = read_files(files)
    make_thread(path, posts)
