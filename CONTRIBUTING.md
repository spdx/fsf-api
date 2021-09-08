# Contributing Guide

## Reporting Issues

`fsf-api` has a [project page on GitHub](https://github.com/spdx/fsf-api) where you can [create an issue](https://github.com/spdx/fsf-api/issues/new/choose) to report a bug, make a suggestion, or propose a substantial change or improvement that you might like to make.
You may also wish to contact the SPDX working group technical team through its mailing list, [spdx-tech@lists.spdx.org](mailto:spdx-tech@lists.spdx.org).

If you would like to work on a fix for any issue, please assign the issue to yourself prior to creating a Pull Request.

## Submitting Pull Requests

The `master` branch of this repository contains [the pulling script](pull.py) and associated documentation.
Please review [open pull requests](https://github.com/spdx/fsf-api/pulls) and [active branches](https://github.com/spdx/fsf-api/branches) before committing time to a substantial revision.
Work along similar lines may already be in progress.

To submit a pull request via GitHub, fork the repository, create a topic branch from `master` for your work, and send a pull request when ready.
If you would prefer to send a patch or grant access to pull from your own Git repository, please contact the project's contributors by email.

The extracted data is in the `gh-pages` branch.

To generate a pull request for the data, clone the gh-pages branch into a separate directory:

    $ git clone -b gh-pages https://github.com/spdx/fsf-api.git data
	
Run the pull.py script with the data directory as the parameter:

	$ python ../fsf-api/pull.py data

You can then create a pull request for the updated data.

## Signing Your Changes

However you choose to contribute, please sign-off each of your commits to certify them under the terms of the [Developer Certificate of Origin](https://developercertificate.org/).
Git has built-in support for signing off: `git commit -s` signs a current commit, and `git rebase --signoff <revision-range>` retroactively signs a range of past commits.

The content of the `master` branch is available under [the MIT license](LICENSE.md).
