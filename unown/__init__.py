# Unown is an EPUB generation utility conforming to EPUB 3.0.
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
import zipfile
import uuid
import datetime

import os.path as op

from dataclasses import dataclass, field
from typing import List
from fnmatch import fnmatch

import jinja2
import tomlkit as toml

env = jinja2.Environment(loader=jinja2.PackageLoader('unown', 'templates'))

mime = {
    'html': 'application/xhtml+xml',
    'xhtml': 'application/xhtml+xml',
    'png':  'image/png',
    'jpg':  'image/jpeg',
    'css':  'text/css',
    'xml':  'application/xml',
    'ttf':  'font/ttf',
}

@dataclass
class File:
    path: str
    name: str
    nav: bool = None

    @property
    def xhtml_filename(self):
        name, ext = op.splitext(self.name)
        return name + '.xhtml'

    @property
    def samedir(self):
        path = op.split(self.name)[-1]
        name, ext = op.splitext(path)
        return name + '.xhtml'

    @property
    def mime(self):
        name, ext = op.splitext(self.name)
        return mime[ext[1:]]

    @property
    def readable(self):
        return self.name.endswith('.html')

    @property
    def id(self):
        path = 'post' + op.split(self.name)[-1]
        name, ext = op.splitext(path)
        return name

    @property
    def title(self):
        path = 'Chapter ' + op.split(self.name)[-1]
        name, ext = op.splitext(path)
        return name

@dataclass
class Book:
    title: str
    language: str
    copyright: int
    creator: str
    uuid: str
    subtitle: str = None
    generated: str = None
    contributors: List[str] = field(default_factory=list)
    items: List[File] = field(default_factory=list)

def load_config(filename):
    with open(filename, mode='r') as f:
        cfg = toml.loads(f.read())

    # EPUB requires a unique identifier, and since we're not published yet,
    # a UUID will have to do.
    if 'uuid' not in cfg:
        cfg['uuid'] = str(uuid.uuid1())

    return cfg

def save_config(filename, cfg):
    with open(filename, mode='w') as f:
        f.write(toml.dumps(cfg))

def generate_filelist_from_path(path, metadata=False):
    files = []
    oebps_present = False
    meta_present = False

    with os.scandir(path) as d:
        for entry in d:
            if entry.is_dir():
                if entry.name == 'OEBPS':
                    oebps_present = True
                elif entry.name == 'META-INF':
                    meta_present = True
                continue

            files.append(File(path, entry.name))

    if oebps_present:
        with os.scandir(op.join(path, 'OEBPS')) as d:
            for entry in d:
                if entry.is_dir():
                    continue
                files.append(File(path, op.join('OEBPS', entry.name)))

    if meta_present and metadata:
        with os.scandir(op.join(path, 'META-INF')) as d:
            for entry in d:
                if entry.is_dir():
                    continue
                files.append(File(path, op.join('META-INF', entry.name)))

    return files

def generate_filelist_from_includes(path, includes):
    files = []

    for item in includes:
        full_name = op.join(path, item)
        if not op.exists(full_name):
            raise ValueError('{} missing'.format(item))

        if '/' in item:
            tree = op.split(full_name)
            name = tree[-1]
            path = op.join(tree[:-2])
        else:
            name = item

        files.append(File(path, name))

    return files

def generate_filelist_from_excludes(path, excludes):
    files = []

    with os.scandir(path) as d:
        for entry in d:
            if entry.name in excludes:
                continue
            else:
                files.append(File(path, entry.name))

    return files

def generate_filelist_with_filter(path, items, includes=True):
    if includes:
        files = generate_filelist_from_includes(
            op.join(path, 'OEBPS'),
            items
        )
    else:
        files = generate_filelist_from_excludes(
            op.join(path, 'OEBPS'),
            items
        )

    with os.scandir(path) as d:
        for outer in d:
            if outer.name == 'META-INF' and outer.is_dir():
                with os.scandir(op.join(path, outer.name)) as e:
                    for inner in e:
                        files.append(File(op.join(path, outer.name), inner.name))
            elif outer.name == 'OEBPS' and outer.is_dir():
                with os.scandir(op.join(path, outer.name)) as e:
                    for inner in e:
                        if inner.name == 'nav.xhtml' and includes:
                            files.append(File(op.join(path, outer.name), inner.name, nav=True))
            else:
                files.append(File(path, outer.name))

    return files

def build_package(cfg, path, files=None, mode='all', pkg_uuid=None):
    if mode not in ['include', 'exclude', 'all']:
        raise ValueError('unknown mode')

    package = op.join(path, 'epub.opf')
    toc = op.join(path, 'nav.xhtml')
    book = Book(
        title=cfg['title'],
        subtitle=cfg['subtitle'],
        language=cfg['language'],
        copyright=cfg['copyright'],
        creator=cfg['creator'],
        contributors=cfg['contributors'],
        uuid=pkg_uuid if pkg_uuid is not None else cfg['uuid'],
        generated=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    )

    if not op.exists(op.join(path, 'META-INF')):
        os.mkdir(op.join(path, 'META-INF'))

    if op.exists(package): os.unlink(package)

    if mode == 'all':
        files = generate_filelist_from_path(path)
    elif mode == 'include':
        files = generate_filelist_from_includes(op.join(path, 'OEBPS'), files)
    elif mode == 'exclude':
        files = generate_filelist_from_excludes(op.join(path, 'OEBPS'), files)

    def key(item):
        return item.name
    book.items = sorted(files, key=key)

    for item in book.items:
        if item.name == 'nav.xhtml':
            book.items.remove(item)
            book.items.insert(0, item)
            break

    if not op.exists(toc):
        with open(toc, mode='w') as f:
            f.write(env.get_template('nav.html').render(package=book))

    with open(package, mode='w') as f:
        f.write(env.get_template('package.xml').render(package=book))

def build_package_singleton(cfg, path, mode='all'):
    if mode not in ['white', 'black', 'all']:
        raise ValueError('unknown mode')

    package = op.join(path, 'epub.opf')
    toc = op.join(path, 'OEBPS', 'nav.xhtml')
    book = Book(
        title=cfg['title'],
        subtitle=cfg['subtitle'],
        language=cfg['language'],
        copyright=cfg['copyright'],
        creator=cfg['creator'],
        contributors=cfg['contributors'],
        uuid=cfg['uuid'],
        generated=datetime.datetime.now(datime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    )
    files = [File(path, cfg['source'])]

    files.append(generate_toc_from_file(op.join(path, cfg['source']), toc))
    book.items = files

    with open(package, mode='w') as f:
        f.write(env.get_template('package.xml').render(package=book))

def make_zip(filename, path, files=None, mode='all'):
    doc = zipfile.ZipFile(
        filename,
        mode='x',
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9
    )
    doc.writestr('mimetype', 'application/epub+zip',
            compress_type=zipfile.ZIP_STORED)
    doc.writestr('META-INF/container.xml', env.get_template('container.xml').render())

    if mode == 'all':
        files = generate_filelist_from_path(path)
    elif mode == 'include':
        files = generate_filelist_with_filter(path, files, includes=True)
    elif mode == 'exclude':
        files = generate_filelist_with_filter(path, files, includes=False)
    else:
        raise ValueError('unrecognized mode: {}'.format(mode))

    for file in files:
        name = file.name
        if (
            name.endswith('.png') or name.endswith('.jpg') or
            name.endswith('.ttf')
        ):
            compress = zipfile.ZIP_STORED
        elif name.endswith('.html'):
            name = file.xname
            compress = zipfile.ZIP_DEFLATED
        else:
            compress = zipfile.ZIP_DEFLATED

        name = file.xhtml_filename if file.name.endswith('.html') else file.name

        doc.write(op.join(file.path, file.name), name, compress_type=compress, compresslevel=9)
