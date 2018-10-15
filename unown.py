#!/usr/bin/env python3
#
# Unown is an EPUB generation utility conforming to EPUB 3.0.
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
    'xml':  'application/xml'
}

@dataclass
class File:
    path: str
    name: str
    nav: bool = None

    @property
    def xname(self):
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
        path = 'Post ' + op.split(self.name)[-1]
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

def generate_filelist_from_whitelist(path, whitelist):
    files = []

    for item in whitelist:
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

def generate_filelist_from_blacklist(path, blacklist):
    files = []

    with os.scandir(path) as d:
        for entry in d:
            if entry.name in blacklist:
                continue
            else:
                files.append(File(path, entry.name))

    return files

def generate_filelist_with_filter(path, items, whitelist=True):
    if whitelist:
        files = generate_filelist_from_whitelist(
            op.join(path, 'OEBPS'),
            items
        )
    else:
        files = generate_filelist_from_blacklist(
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
                        if inner.name == 'nav.xhtml' and whitelist:
                            files.append(File(op.join(path, outer.name), inner.name, nav=True))
            else:
                files.append(File(path, outer.name))

    return files

def build_package(cfg, path, files=None, whitelist=True):
    package = op.join(path, cfg['directory'], 'epub.opf')
    toc = op.join(path, cfg['directory'], 'OEBPS', 'nav.xhtml')
    book = Book(
        title=cfg['title'],
        subtitle=cfg['subtitle'],
        language=cfg['language'],
        copyright=cfg['copyright'],
        creator=cfg['creator'],
        contributors=cfg['contributors'],
        uuid=cfg['uuid'],
        generated=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    )

    if not op.exists(op.join(path, cfg['directory'], 'META-INF')):
        os.mkdir(op.join(path, cfg['directory'], 'META-INF'))

    if op.exists(package):
        os.unlink(package)
    if op.exists(toc):
        os.unlink(toc)

    if files is None:
        files = generate_filelist_from_path(op.join(path, cfg['directory']))
    elif whitelist:
        files = generate_filelist_from_whitelist(op.join(path, cfg['directory'], 'OEBPS'), files)
    else:
        files = generate_filelist_from_blacklist(op.join(path, cfg['directory'], 'OEBPS'), files)

    book.items = files

    with open(op.join(path, cfg['directory'], 'OEBPS', 'nav.xhtml'), mode='w') as f:
        f.write(env.get_template('nav.html').render(package=book))

    book.items.append(File(op.join(path, cfg['directory'], 'OEBPS'), 'nav.xhtml', nav=True))

    with open(package, mode='w') as f:
        f.write(env.get_template('package.xml').render(package=book))

def make_zip(filename, filelist):
    doc = zipfile.ZipFile(
        filename,
        mode='x',
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9
    )
    doc.writestr('mimetype', 'application/epub+zip')
    doc.write('templates/container.xml', 'META-INF/container.xml', compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    for file in filelist:
        if file.name.endswith('.png') or file.name.endswith('.jpg'):
            compress = zipfile.ZIP_STORED
        else:
            compress = zipfile.ZIP_DEFLATED

        name = file.xname if file.name.endswith('.html') else file.name

        doc.write(op.join(file.path, file.name), name, compress_type=compress, compresslevel=9)

if __name__ == '__main__':
    import sys

    print('Loading configuration...')
    cfg = load_config(sys.argv[1])
    print('Generating EPUB for {}{}...'.format(
        cfg['title'],
        ': {}'.format(cfg['subtitle']) if 'subtitle' in cfg.keys() else ''
    ))
    if 'whitelist' in cfg.keys():
        filtered = True
        root_uuid = cfg['uuid']
        pkgs = [item for item in cfg['whitelist'].keys() if not item.endswith('_uuid')]
        output_base = op.splitext(sys.argv[2])

        print('Found {} whitelist{}.'.format(len(pkgs), 's' if len(pkgs) > 1 else ''))
        for name in pkgs:
            whitelist = cfg['whitelist'][name]
            output = ''.join([output_base[0] + '_' + name, output_base[1]])

            if '{}_uuid'.format(name) not in cfg['whitelist']:
                cfg['whitelist']['{}_uuid'.format(name)] = str(uuid.uuid1())

            # FIXME - this is gross
            cfg['uuid'] = cfg['whitelist']['{}_uuid'.format(name)]
            print('  Building EPUB Package Document for subset "{}"...'.format(name))
            build_package(cfg, '.', list(whitelist), whitelist=True)
            cfg['uuid'] = root_uuid

            print('  Building EPUB Container for subset "{}"...'.format(name))
            make_zip(output, generate_filelist_with_filter(
                op.join('.', cfg['directory']),
                list(whitelist),
                whitelist=True
            ))

        save_config(sys.argv[1], cfg)
    if 'blacklist' in cfg.keys():
        filtered = True
        root_uuid = cfg['uuid']
        pkgs = [item for item in cfg['blacklist'].keys() if not item.endswith('_uuid')]
        output_base = op.splitext(sys.argv[2])

        print('Found {} blacklist{}.'.format(len(pkgs), 's' if len(pkgs) > 1 else ''))
        for name in pkgs:
            blacklist = cfg['blacklist'][name]
            output = ''.join([output_base[0] + '_' + name, output_base[1]])

            if '{}_uuid'.format(name) not in cfg['blacklist']:
                cfg['blacklist']['{}_uuid'.format(name)] = str(uuid.uuid1())

            # FIXME - this is gross
            cfg['uuid'] = cfg['blacklist']['{}_uuid'.format(name)]
            print('  Building EPUB Package Document for subset "{}"...'.format(name))
            build_package(cfg, '.', list(blacklist), whitelist=False)
            cfg['uuid'] = root_uuid

            print('  Building EPUB Container for subset "{}"...'.format(name))
            make_zip(output, generate_filelist_with_filter(
                op.join('.', cfg['directory']),
                list(blacklist),
                whitelist=False
            ))

        save_config(sys.argv[1], cfg)
    
    if cfg['generate_all'] or not filtered:
        print('Building EPUB Package Document for {}...'.format(cfg['title']))
        build_package(cfg, '.')
        print('Building EPUB Container...')
        make_zip(sys.argv[2], generate_filelist_from_path(op.join('.', cfg['directory']), metadata=True))
        print('Saving configuration...')
        save_config(sys.argv[1], cfg)
