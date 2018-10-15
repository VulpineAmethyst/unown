#!/usr/bin/env python3
#
# extract_4chan.py extracts posts from 4chan threads.
# Copyright (C) 2018 Kiyoshi Aman
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
import re

import os.path as op

from dataclasses import dataclass
from xml.etree import ElementTree

import lxml.html.soupparser as parser
import jinja2

env = jinja2.Environment(loader=jinja2.PackageLoader('unown', 'templates'))

@dataclass
class Post:
    id: int
    author: str
    content: str
    date: str
    attachment: str = None

    def to_html(self):
        template = env.get_template('post.html')

        return template.render(post=self)

def parse_html(file):
    html = parser.parse(file)

    # extract the thread ID
    thread_id = html.xpath('//form/a[@name][1]/@name')
    thread_posts = html.xpath('count(//form/a[@name])')

    posts = []
    post_ids = html.xpath('//td[@class="reply"]/@id')

    # first post is special, unfortunately.
    post_id = post_ids.pop(0)
    author  = html.xpath('//form/span[@class="postername"][1]/text()')[0]
    content = ElementTree.tostring(html.xpath('//form/blockquote')[0]).decode('UTF-8')
    date    = html.xpath('//form/span[@class="posttime"][1]/text()')[0]
    attach  = html.xpath('//form/span[@class="filesize"]/a[1]/@href')
    attach  = attach[0] if len(attach) > 0 else None
    posts.append(Post(post_id, author, content, date, attach))

    # <a class="quotelink unkfunc" href="http://suptg.thisisnotatrueending.com/archive/17738107/#17745349" onclick="replyhl('17745349');">&gt;&gt;17745349</a>
    magic = re.compile(r'<a class=".*?" href=".*?" onclick=".*?">(.*?)</a>')

    # extract other postss
    for post in post_ids:
        author  = html.xpath('//td[@id={}]/span[@class="commentpostername"]/text()'.format(post))[0]
        content = ElementTree.tostring(html.xpath('//td[@id={}]/blockquote'.format(post))[0]).decode('UTF-8')
        date    = html.xpath('//td[@id={}][span[@class="commentpostername"]]/text()[string-length()>1][1]'.format(post))[0]
        attach  = html.xpath('//td[@id={}][span[@class="filesize"]]/a/@href'.format(post))
        attach  = attach[0] if len(attach) > 0 else None

        content = magic.sub(r'\\1', content)

        posts.append(Post(post, author, content, date, attach))

    return posts

def output_posts(directory, posts):
    for post in posts:
        print("Writing post {}...".format(post.id))

        with open(op.join(directory, str(post.id) + '.html'), mode='w') as f:
            f.write(post.to_html())

if __name__ == '__main__':
    import sys

    filename  = sys.argv[1]
    outputdir = sys.argv[2]

    output_posts(outputdir, parse_html(filename))
