# FSF License Metadata API

The FSF is [interested in having the SPDX expose some of its metadata in the SPDX license list][fsf-api].
The cleanest way to do that is to have the FSF provide [their annotated license list][fsf-list] in a format that is more convenient for automated tools.
For example, [the OSI provides an API][osi-api] which, while [currently][osi-api-noncanon-1] [non-canonical][osi-api-non-canon-2], provides convenient access to OSI license annotations.

This repository scrapes the FSF list and provides the scraped data in a JSON API for others to consume.
Ideally we'll hand this repository over to the FSF once they're ready to maintain it, or we'll deprecate this repository if they decide to provide a different API.

## Endpoints

<a name="licenses.json"></a>
You can pull an array of identifiers from [https://spdx.github.io/fsf-api/licenses.json](https://spdx.github.io/fsf-api/licenses.json).

<a name="licenses-full.json"></a>
You can pull an object with all the license data [https://spdx.github.io/fsf-api/licenses-full.json](https://spdx.github.io/fsf-api/licenses-full.json).

You can pull an individual license from a few places:

* <a name="by-fsf-id"></a>
    Using their FSF ID:

        https://spdx.github.io/fsf-api/{id}.json

    For example [https://spdx.github.io/fsf-api/Expat.json](https://spdx.github.io/fsf-api/Expat.json).

* <a name="by-non-fsf-id"></a>
    Using a non-FSF ID, according to the mapping between other scheme and the FSF scheme asserted by this API:

        https://spdx.github.io/fsf-api/{scheme}/{id}.json

    For example [https://spdx.github.io/fsf-api/spdx/MIT.json](https://spdx.github.io/fsf-api/spdx/MIT.json).
    This API currently [attempts](#caveats) to maintain the following mappings:

    * `spdx`, using [the SPDX identifiers][spdx-list].

## License properties

Licenses have the following properties:

* `id`: a short slug identifying the license.
    In [`licenses-full.json`](#licenses-full.json), this is information is in the in root object key and not duplicated in the value.
* `name`: a short string naming the license.
* `uris`: an array of URIs for the license.
    The first entry in this array will always be an entry on the [the FSF's HTML page][fsf-list].
    The order of the remaining entries is not significant.
* `tags`: an array of FSF categories for the license.
    The FSF currently defines the following categories:

    * `gpl-2-compatible` and `gpl-3-compatible`: [licenses that are GPL-compatible][fsf-list-gpl-compatible].
    * `fdl-compatible`: [licenses that are FDL-compatible][fsf-list-fdl-compatible].
    * `libre`: licenses that are either [GPL-compatible][fsf-list-gpl-compatible], [FDL-compatible][fsf-list-fdl-compatible], [or][fsf-list-free-software] [are][fsf-list-free-documentation] [otherwise][fsf-list-practical] [free][fsf-list-font].
    * `viewpoint`: [licenses for works stating a viewpoint][fsf-list-viewpoint].
    * `non-free`: licenses that [are][fsf-list-non-free-software] [non-free][fsf-list-non-free-documentation].
* `identifiers`: an object with mappings to other license lists.
    This API currently [attempts](#caveats) to maintain the following mappings:

    * `spdx`: For licenses with SPDX IDs, the `spdx` value will hold an array of [SPDX identifiers][spdx-list].
        Licenses may have multiple SPDX entries when SPDX list defines per-grant IDs that share the same license (e.g. [`GPL-3.0-only`][spdx-gpl-3.0-only] and [`GPL-3.0-or-later`][spdx-gpl-3.0-or-later]).
        The first entry in the SPDX array is the one that most closely matches the FSF license.
        For example, the FSF's [`GNUGPLv3`][fsf-gplv3] text has:

        > However, most software released under GPLv2 allows you to use the terms of later versions of the GPL as well.

        and the GPLv3 text [suggests an “any later version” grant][gplv3-howto], so `GPL-3.0-or-later` is the first SPDX identifier, `GPL-3.0-only` is the second, and the deprecated `GPL-3.0` is the third.

## Caveats

There are currently some hacks in [the pulling script](pull.py):

* `SPLITS`, which:

    * Unpacks some places where [the FSF's HTML page][fsf-list] uses a single identifier for multiple licenses (e.g. [using `AcademicFreeLicense` for “all versions through 3.0”][fsf-afl]).
    * Repacks places where [the FSF's HTML page][fsf-list] uses two identifiers for the same license (e.g. to classify `FreeBSD` as both [GPL-compatible][fsf-freebsd-gpl] and [FDL-compatible][fsf-freebsd-fdl]).

* `IDENTIFIERS`, which maps FSF identifiers to other schemes.
    Ideally this would be based on [automated license-text comparison][automated-matching], but in order for that to work this API would have to expose the license text that the FSF considered for each ID.
    Currently, [the FSF's HTML page][fsf-list] links to license source, but not in a consistent enough way for me to extract the text.

* `TAG_OVERRIDES`, which sets `tags` where the human-readable text on the [FSF's annotated list][fsf-list] has more detail than the easily-machine-readable content.
    For example, the FSF currently only distinguishes between `gpl-2-compatible` and `gpl-3-compatible` in text, so licenses that are only compatible with one or the other need tag overrides.

Until these hacks are addressed, license IDs and the `tags` and `identifiers` fields should be taken with a grain of salt.

## Credits
The original implementation of the fsf-api was provided by @wking.  This repository is now being maintained by the SPDX community.

## Contributing

[Contributions](CONTRIBUTING.md) are welcome!

[automated-matching]: https://github.com/spdx/license-list-XML/issues/418
[fsf-afl]: https://www.gnu.org/licenses/license-list.html#AcademicFreeLicense
[fsf-api]: https://lists.spdx.org/pipermail/spdx-legal/2017-October/002281.html
[fsf-freebsd-fdl]: https://www.gnu.org/licenses/license-list.html#FreeBSDDL
[fsf-freebsd-gpl]: https://www.gnu.org/licenses/license-list.html#FreeBSD
[fsf-gplv3]: https://www.gnu.org/licenses/license-list.html#GNUGPLv3
[fsf-list]: https://www.gnu.org/licenses/license-list.html
[fsf-list-gpl-compatible]: https://www.gnu.org/licenses/license-list.html#GPLCompatibleLicenses
[fsf-list-fdl-compatible]: https://www.gnu.org/licenses/license-list.html#FDL
[fsf-list-free-software]: https://www.gnu.org/licenses/license-list.html#GPLIncompatibleLicenses
[fsf-list-non-free-software]: https://www.gnu.org/licenses/license-list.html#NonFreeSoftwareLicenses
[fsf-list-free-documentation]: https://www.gnu.org/licenses/license-list.html#FreeDocumentationLicenses
[fsf-list-non-free-documentation]: https://www.gnu.org/licenses/license-list.html#NonFreeDocumentationLicenses
[fsf-list-practical]: https://www.gnu.org/licenses/license-list.html#GPLOther
[fsf-list-font]: https://www.gnu.org/licenses/license-list.html#Fonts
[fsf-list-viewpoint]: https://www.gnu.org/licenses/license-list.html#OpinionLicenses
[gplv3-howto]: https://www.gnu.org/licenses/gpl.html#howto
[osi-api-non-canon-2]: https://github.com/OpenSourceOrg/licenses/issues/47
[osi-api-noncanon-1]: https://github.com/OpenSourceOrg/licenses/tree/f7ff223f9694ca0d5114fc82e43c74b5c5087891#is-this-authoritative
[osi-api]: https://api.opensource.org/
[spdx-list]: https://spdx.org/licenses/
[spdx-gpl-3.0-only]: https://spdx.org/licenses/GPL-3.0-only.html
[spdx-gpl-3.0-or-later]: https://spdx.org/licenses/GPL-3.0-or-later.html
