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

import sys

import os.path as op

import unown

print('Loading configuration...')
cfg = unown.load_config(sys.argv[1])
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
        unown.build_package(cfg, '.', list(whitelist), whitelist=True)
        cfg['uuid'] = root_uuid

        print('  Building EPUB Container for subset "{}"...'.format(name))
        unown.make_zip(output, unown.generate_filelist_with_filter(
            op.join('.', cfg['directory']),
            list(whitelist),
            whitelist=True
        ))

    unown.save_config(sys.argv[1], cfg)
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
        unown.build_package(cfg, '.', list(blacklist), whitelist=False)
        cfg['uuid'] = root_uuid

        print('  Building EPUB Container for subset "{}"...'.format(name))
        unown.make_zip(output, unown.generate_filelist_with_filter(
            op.join('.', cfg['directory']),
            list(blacklist),
            whitelist=False
        ))

    unown.save_config(sys.argv[1], cfg)

if cfg['generate_all'] or not filtered:
    print('Building EPUB Package Document for {}...'.format(cfg['title']))
    unown.build_package(cfg, '.')
    print('Building EPUB Container...')
    unown.make_zip(
        sys.argv[2],
        unown.generate_filelist_from_path(
            op.join('.', cfg['directory']),
            metadata=True
        )
    )
    print('Saving configuration...')
    unown.save_config(sys.argv[1], cfg)
