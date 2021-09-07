#!/usr/bin/env python3
#
# SPDX-License-Identifier: MIT

"""Generate the FSF license API JSON data from the FSF license list page."""

import argparse
import glob
import html
import io
import json
import os
import re
import urllib.parse
import urllib.request

import lxml.etree


SOURCE_URI = 'https://www.gnu.org/licenses/license-list.html'
API_BASE_URI = 'https://spdx.github.io/fsf-api/'

TAGS = {
    'blue': {'viewpoint'},
    'green': {'gpl-2-compatible', 'gpl-3-compatible', 'libre'},
    'orange': {'libre'},
    'purple': {'fdl-compatible', 'libre'},
    'red': {'non-free'},
}

SPLITS = {
    'AcademicFreeLicense': [  # all versions through 3.0
        'AcademicFreeLicense1.1',
        'AcademicFreeLicense1.2',
        'AcademicFreeLicense2.0',
        'AcademicFreeLicense2.1',
        'AcademicFreeLicense3.0',
    ],
    'CC-BY-NC': [  # any version (!)
        'CC-BY-NC-1.0',
        'CC-BY-NC-2.0',
        'CC-BY-NC-2.5',
        'CC-BY-NC-3.0',
        'CC-BY-NC-4.0',
    ],
    'CC-BY-ND': [  # any version
        'CC-BY-ND-1.0',
        'CC-BY-ND-2.0',
        'CC-BY-ND-2.5',
        'CC-BY-ND-3.0',
        'CC-BY-ND-4.0',
    ],
    'ccbynd': ['CC-BY-ND-4.0'],  # unify (multi-tag)
    'FDL': [
        'FDLv1.1',
        'FDLv1.2',
        'FDLv1.3',
    ],
    'FDLOther': [  # unify with FDL (multi-tag)
        'FDLv1.1',
        'FDLv1.2',
        'FDLv1.3',
    ],
    'FreeBSDDL': ['FreeBSD'],  # unify (multi-tag)
    'NPL': [  # versions 1.0 and 1.1
        'NPL-1.0',
        'NPL-1.1',
    ],
    'OSL': [  # any version through 3.0
        'OSL-1.0',
        'OSL-1.1',
        'OSL-2.0',
        'OSL-2.1',
        'OSL-3.0',
    ],
    'PythonOld': [  # 1.6b1 through 2.0 and 2.1
        'Python1.6b1',
        'Python2.0',
        'Python2.1',
    ],
    'SILOFL': [  # title has 1.1 but text says the same metadata applies to 1.0
        'SILOFL-1.0',
        'SILOFL-1.1',
    ],
    'Zope2.0': [  # versions 2.0 and 2.1
        'Zope2.0',
        'Zope2.1',
    ],
}

TAG_OVERRIDES = {
    'AGPLv3.0': {'libre', 'gpl-3-compatible'},
    'ECL2.0': {'libre', 'gpl-3-compatible'},
    'freetype': {'libre', 'gpl-3-compatible'},
    'GNUGPLv3': {'libre', 'gpl-3-compatible'},
    'GPLv2': {'libre', 'gpl-2-compatible'},
    'LGPLv3': {'libre', 'gpl-3-compatible'},
    'apache2': {'libre', 'gpl-3-compatible'},
}

IDENTIFIERS = {
    'AGPLv1.0': {'spdx': ['AGPL-1.0']},
    'AGPLv3.0': {'spdx': ['AGPL-3.0-or-later', 'AGPL-3.0-only', 'AGPL-3.0']},
    'AcademicFreeLicense1.1': {'spdx': ['AFL-1.1']},
    'AcademicFreeLicense1.2': {'spdx': ['AFL-1.2']},
    'AcademicFreeLicense2.0': {'spdx': ['AFL-2.0']},
    'AcademicFreeLicense2.1': {'spdx': ['AFL-2.1']},
    'AcademicFreeLicense3.0': {'spdx': ['AFL-3.0']},
    'Aladdin': {'spdx': ['Aladdin']},
    'apache1.1': {'spdx': ['Apache-1.1']},
    'apache1': {'spdx': ['Apache-1.0']},
    'apache2': {'spdx': ['Apache-2.0']},
    'apsl1': {'spdx': ['APSL-1.0']},
    'apsl2': {'spdx': ['APSL-2.0']},
    'ArtisticLicense': {'spdx': ['Artistic-1.0']},
    'ArtisticLicense2': {'spdx': ['Artistic-2.0']},
    'BerkeleyDB': {'spdx': ['Sleepycat']},
    'bittorrent': {'spdx': ['BitTorrent-1.1']},
    'boost': {'spdx': ['BSL-1.0']},
    'ccby': {'spdx': ['CC-BY-4.0']},
    'CC-BY-NC-1.0': {'spdx': ['CC-BY-NC-1.0']},
    'CC-BY-NC-2.0': {'spdx': ['CC-BY-NC-2.0']},
    'CC-BY-NC-2.5': {'spdx': ['CC-BY-NC-2.5']},
    'CC-BY-NC-3.0': {'spdx': ['CC-BY-NC-3.0']},
    'CC-BY-NC-4.0': {'spdx': ['CC-BY-NC-4.0']},
    'CC-BY-ND-1.0': {'spdx': ['CC-BY-ND-1.0']},
    'CC-BY-ND-2.0': {'spdx': ['CC-BY-ND-2.0']},
    'CC-BY-ND-2.5': {'spdx': ['CC-BY-ND-2.5']},
    'CC-BY-ND-3.0': {'spdx': ['CC-BY-ND-3.0']},
    'CC-BY-ND-4.0': {'spdx': ['CC-BY-ND-4.0']},
    'ccbysa': {'spdx': ['CC-BY-SA-4.0']},
    'CC0': {'spdx': ['CC0-1.0']},
    'CDDL': {'spdx': ['CDDL-1.0']},
    'CPAL': {'spdx': ['CPAL-1.0']},
    'CeCILL': {'spdx': ['CECILL-2.0']},
    'CeCILL-B': {'spdx': ['CECILL-B']},
    'CeCILL-C': {'spdx': ['CECILL-C']},
    'ClarifiedArtistic': {'spdx': ['ClArtistic']},
    'clearbsd': {'spdx': ['BSD-3-Clause-Clear']},
    'CommonPublicLicense10': {'spdx': ['CPL-1.0']},
    'cpol': {'spdx': ['CPOL-1.02']},
    'Condor': {'spdx': ['Condor-1.1']},
    'ECL2.0': {'spdx': ['ECL-2.0']},
    'eCos11': {'spdx': ['RHeCos-1.1']},
    'eCos2.0': {'spdx': ['GPL-2.0+ WITH eCos-exception-2.0', 'eCos-2.0']},
    'EPL': {'spdx': ['EPL-1.0']},
    'EPL2': {'spdx': ['EPL-2.0']},
    'EUDataGrid': {'spdx': ['EUDatagrid']},
    'EUPL-1.1': {'spdx': ['EUPL-1.1']},
    'EUPL-1.2': {'spdx': ['EUPL-1.2']},
    'Eiffel': {'spdx': ['EFL-2.0']},
    'Expat': {'spdx': ['MIT']},
    'FDLv1.1': {'spdx': ['GFDL-1.1-or-later', 'GFDL-1.1-only', 'GFDL-1.1']},
    'FDLv1.2': {'spdx': ['GFDL-1.2-or-later', 'GFDL-1.2-only', 'GFDL-1.2']},
    'FDLv1.3': {'spdx': ['GFDL-1.3-or-later', 'GFDL-1.3-only', 'GFDL-1.3']},
    'FreeBSD': {'spdx': ['BSD-2-Clause-FreeBSD', 'BSD-2-Clause', 'BSD-2-Clause-NetBSD']},
    'freetype': {'spdx': ['FTL']},
    'GNUAllPermissive': {'spdx': ['FSFAP']},
    'GNUGPLv3': {
        'spdx': ['GPL-3.0-or-later', 'GPL-3.0-only', 'GPL-3.0', 'GPL-3.0+']
    },
    'gnuplot': {'spdx': ['gnuplot']},
    'GPLv2': {
        'spdx': ['GPL-2.0-or-later', 'GPL-2.0-only', 'GPL-2.0', 'GPL-2.0+']
    },
    'HPND': {'spdx': ['HPND']},
    'IBMPL': {'spdx': ['IPL-1.0']},
    'iMatix': {'spdx': ['iMatix']},
    'imlib': {'spdx': ['Imlib2']},
    'ijg': {'spdx': ['IJG']},
    'intel': {'spdx': ['Intel']},
    'IPAFONT': {'spdx': ['IPA']},
    'ISC': {'spdx': ['ISC']},
    'JSON': {'spdx': ['JSON']},
    'LGPLv3': {
        'spdx': ['LGPL-3.0-or-later', 'LGPL-3.0-only', 'LGPL-3.0', 'LGPL-3.0+']
    },
    'LGPLv2.1': {
        'spdx': ['LGPL-2.1-or-later', 'LGPL-2.1-only', 'LGPL-2.1', 'LGPL-2.1+']
    },
    'LPPL-1.2': {'spdx': ['LPPL-1.2']},
    'LPPL-1.3a': {'spdx': ['LPPL-1.3a']},
    'lucent102': {'spdx': ['LPL-1.02']},
    'ModifiedBSD': {'spdx': ['BSD-3-Clause']},
    'MPL': {'spdx': ['MPL-1.1']},
    'MPL-2.0': {'spdx': ['MPL-2.0']},
    'ms-pl': {'spdx': ['MS-PL']},
    'ms-rl': {'spdx': ['MS-RL']},
    'NASA': {'spdx': ['NASA-1.3']},
    'NCSA': {'spdx': ['NCSA']},
    'newOpenLDAP': {'spdx': ['OLDAP-2.7']},
    'Nokia': {'spdx': ['Nokia']},
    'NoLicense': {'spdx': ['NONE']},
    'NOSL': {'spdx': ['NOSL']},
    'NPL-1.0': {'spdx': ['NPL-1.0']},
    'NPL-1.1': {'spdx': ['NPL-1.1']},
    'ODbl': {'spdx': ['ODbL-1.0']},
    'oldOpenLDAP': {'spdx': ['OLDAP-2.3']},
    'OpenPublicL': {'spdx': ['OPL-1.0']},
    'OpenSSL': {'spdx': ['OpenSSL']},
    'OriginalBSD': {'spdx': ['BSD-4-Clause']},
    'OSL-1.0': {'spdx': ['OSL-1.0']},
    'OSL-1.1': {'spdx': ['OSL-1.1']},
    'OSL-2.0': {'spdx': ['OSL-2.0']},
    'OSL-2.1': {'spdx': ['OSL-2.1']},
    'OSL-3.0': {'spdx': ['OSL-3.0']},
    'PHP-3.01': {'spdx': ['PHP-3.01']},
    'Python2.0': {'spdx': ['Python-2.0']},
    'QPL': {'spdx': ['QPL-1.0']},
    'RPSL': {'spdx': ['RPSL-1.0']},
    'Ruby': {'spdx': ['Ruby']},
    'SGIFreeB': {'spdx': ['SGI-B-2.0']},
    'SILOFL-1.0': {'spdx': ['OFL-1.0']},
    'SILOFL-1.1': {'spdx': ['OFL-1.1']},
    'SPL': {'spdx': ['SPL-1.0']},
    'StandardMLofNJ': {'spdx': ['SMLNJ', 'StandardML-NJ']},
    'Unlicense': {'spdx': ['Unlicense']},
    'UPL': {'spdx': ['UPL-1.0']},
    'Vim': {'spdx': ['Vim']},
    'W3C': {'spdx': ['W3C']},
    'Watcom': {'spdx': ['Watcom-1.0']},
    'WTFPL': {'spdx': ['WTFPL']},
    'X11License': {'spdx': ['X11']},
    'XFree861.1License': {'spdx': ['XFree86-1.1']},
    'xinetd': {'spdx': ['xinetd']},
    'Yahoo': {'spdx': ['YPL-1.1']},
    'Zend': {'spdx': ['Zend-2.0']},
    'Zimbra': {'spdx': ['Zimbra-1.3']},
    'ZLib': {'spdx': ['Zlib', 'Nunit']},
    'Zope2.0': {'spdx': ['ZPL-2.0']},
    'Zope2.1': {'spdx': ['ZPL-2.1']},
}


def convert_html_escapes_to_xml(html_text):
    """Avoid XML parsing errors by converting HTML escape codes to XML."""
    html_entities = set(
        re.findall(r'&(?!quot|lt|gt|amp|apos)[a-zA-Z]{1,30};', html_text)
    )
    for entity in html_entities:
        html_text = html_text.replace(entity, html.unescape(entity))
    return html_text


def get(uri):
    """Get the license list page data from the FSF web site."""
    parser = lxml.etree.XMLParser(ns_clean=True, resolve_entities=False)
    with urllib.request.urlopen(uri) as response:
        response_data = response.read().decode()
    response_data = convert_html_escapes_to_xml(response_data)
    response_data_io = io.StringIO(response_data)
    return lxml.etree.parse(response_data_io, base_url=uri, parser=parser)


def extract(root, base_uri=None):
    """Parse the license list page and extract the needed license data."""
    oids = set()
    licenses = {}
    for dl in root.iter(tag='{http://www.w3.org/1999/xhtml}dl'):
        try:
            tags = TAGS[dl.attrib.get('class')]
        except KeyError as error:
            raise ValueError(
                'unrecognized class {!r}'.format(dl.attrib.get('class'))
            ) from error
        for a in dl.iter(tag='{http://www.w3.org/1999/xhtml}a'):
            if 'id' not in a.attrib:
                continue
            oid = a.attrib['id']
            oids.add(oid)
            for license_id in SPLITS.get(oid, [oid]):
                license_data = {
                    'tags': TAG_OVERRIDES.get(license_id, tags).copy(),
                }
                if a.text and a.text.strip():
                    license_data['name'] = a.text.strip()
                else:
                    continue
                uris = [f'{base_uri}#{oid}']
                uri = a.attrib.get('href')
                if uri:
                    if base_uri:
                        uris.append(
                            urllib.parse.urljoin(base=base_uri, url=uri)
                        )
                license_data['uris'] = uris
                identifiers = IDENTIFIERS.get(license_id)
                if identifiers:
                    license_data['identifiers'] = identifiers
                if license_id not in licenses:
                    licenses[license_id] = license_data
                else:
                    licenses[license_id]['tags'].update(tags)
                    for uri in uris:
                        if uri not in licenses[license_id]['uris']:
                            licenses[license_id]['uris'].append(uri)
    unused_splits = set(SPLITS.keys()).difference(oids)
    if unused_splits:
        raise ValueError(
            'unused SPLITS keys: {}'.format(', '.join(sorted(unused_splits)))
        )
    return licenses


def save(licenses, base_uri, output_dir=os.curdir):
    """Save the license data to a files in the appropriate JSON schema."""
    schema_dir = os.path.join(output_dir, 'schema')
    os.makedirs(schema_dir, exist_ok=True)
    paths = glob.glob(os.path.join(output_dir, '**', '*.json'), recursive=True)
    for path in paths:
        os.remove(path)
    license_schema = {
        '@context': {
            'schema': 'https://schema.org/',
            'id': {'@id': 'schema:identifier'},
            'name': {
                '@id': 'schema:name',
            },
            'uris': {
                '@container': '@list',
                '@id': 'schema:url',
            },
            'tags': {
                '@id': 'schema:keywords',
            },
            'identifiers': {
                '@container': '@index',
                '@id': 'schema:identifier',
            },
        },
    }
    with open(
        os.path.join(schema_dir, 'license.jsonld'), 'w', encoding='utf-8'
    ) as f:
        json.dump(obj=license_schema, fp=f, indent=2, sort_keys=True)
        f.write('\n')
    license_schema_uri = urllib.parse.urljoin(
        base=base_uri, url='schema/license.jsonld'
    )
    licenses_schema = license_schema.copy()
    licenses_schema['@context']['licenses'] = {
        '@container': '@index',
        '@id': license_schema_uri,
    }
    licenses_schema.update(license_schema)
    with open(
        os.path.join(schema_dir, 'licenses.jsonld'), 'w', encoding='utf-8'
    ) as f:
        json.dump(obj=licenses_schema, fp=f, indent=2, sort_keys=True)
        f.write('\n')
    licenses_schema_uri = urllib.parse.urljoin(
        base=base_uri, url='schema/licenses.jsonld'
    )
    index = sorted(licenses.keys())
    with open(
        os.path.join(output_dir, 'licenses.json'), 'w', encoding='utf-8'
    ) as f:
        json.dump(obj=index, fp=f, indent=2, sort_keys=True)
        f.write('\n')
    full_index = {
        '@context': licenses_schema_uri,
        'licenses': {},
    }
    for license_id, license_data in licenses.items():
        license_data = license_data.copy()
        if 'tags' in license_data:
            license_data['tags'] = sorted(license_data['tags'])
        license_data['id'] = license_id
        full_index['licenses'][license_id] = license_data.copy()
        license_data['@context'] = urllib.parse.urljoin(
            base=base_uri, url='schema/license.jsonld'
        )
        license_path = os.path.join(output_dir, f'{license_id}.json')
        with open(license_path, 'w', encoding='utf-8') as f:
            json.dump(obj=license_data, fp=f, indent=2, sort_keys=True)
            f.write('\n')
        for scheme, identifiers in license_data.get('identifiers', {}).items():
            scheme_dir = os.path.join(output_dir, scheme)
            os.makedirs(scheme_dir, exist_ok=True)
            if isinstance(identifiers, str):
                identifiers = [identifiers]
            for identifier in identifiers:
                id_path = os.path.join(scheme_dir, f'{identifier}.json')
                os.link(license_path, id_path)
    with open(
        os.path.join(output_dir, 'licenses-full.json'), 'w', encoding='utf-8'
    ) as f:
        json.dump(obj=full_index, fp=f, indent=2, sort_keys=True)
        f.write('\n')


def generate_api(
    output_dir=os.curdir,
    source_uri=SOURCE_URI,
    api_base_uri=API_BASE_URI,
):
    """Load the license list page, parse it and generate the API output."""
    tree = get(uri=source_uri)
    root = tree.getroot()
    licenses = extract(root=root, base_uri=source_uri)
    unused_identifiers = {key for key in IDENTIFIERS if key not in licenses}
    if unused_identifiers:
        raise ValueError(
            'unused IDENTIFIERS keys: {}'.format(
                ', '.join(sorted(unused_identifiers))
            )
        )
    save(
        licenses=licenses,
        base_uri=api_base_uri,
        output_dir=output_dir,
    )


def generate_arg_parser():
    """Create the CLI argument parser object for the script."""
    parser_main = argparse.ArgumentParser(
        description='Generate the FSF license API JSON data.',
        argument_default=argparse.SUPPRESS,
    )
    parser_main.add_argument(
        'output_dir',
        nargs='?',
        help='The directory to output the API data to, the CWD by default',
    )
    parser_main.add_argument(
        '--source-uri',
        help='A custom source URI to load the FSF license list page from',
    )
    parser_main.add_argument(
        '--api-base-uri',
        help='A custom base URL for the output API',
    )
    return parser_main


def main(sys_argv=None):
    """Run the API generation script with the specified CLI options."""
    arg_parser = generate_arg_parser()
    cli_args = arg_parser.parse_args(sys_argv)
    generate_api(**vars(cli_args))


if __name__ == '__main__':
    main()
