# Git-annex special remote for accessing (Remote) Indexed file Archives (RIA)

[![Travis tests status](https://secure.travis-ci.org/datalad/git-annex-ria-remote.png?branch=master)](https://travis-ci.org/datalad/git-annex-ria-remote) [![GitHub release](https://img.shields.io/github/release/datalad/git-annex-ria-remote.svg)](https://GitHub.com/datalad/git-annex-ria-remote/releases/) [![PyPI version fury.io](https://badge.fury.io/py/git-annex-ria-remote.svg)](https://pypi.python.org/pypi/git-annex-ria-remote/)

This [git-annex](http://git-annex.branchable.com) [special
remote](http://git-annex.branchable.com/special_remotes) implementation is very
similar to the `directory` special remote type built into git-annex. There are
a few key differences that outline the use cases where one might consider using
this one instead:

- (Optional) read-access to (compressed) 7z archives

  (Parts of) the keys stored in the remote can live in a
  [7z](https://www.7-zip.org) archive. These archives are indexed and support
  relatively fast random read access. This feature can be instrumental on
  HPC storage systems where strong quotas on filesystem inodes might be imposed
  on users. The entire key store of the remote can be put into an archive, re-using
  the exact same directory structure, and remains fully accessible while only
  using a handful of inodes, regardless of file number and size.

- (SSH-based remote) access to a configurable directory

  An SSH host name can be provided and all interaction with the remote will be
  performed via SSH. Moving from local to remote operations, or switching target
  paths can be done via a change to the configuration (even without having to touch
  a repository at all). This makes it easier to accommodate infrastructural changes,
  especially when dealing with large numbers of repositories.

- Multi-repository directory structure

  While each repository has its own associated key store directory tree, the
  key store directories of multiple repositories can be organized into a homogeneous
  archive directory structure. For [DataLad](http://datalad.org) datasets, their
  ID is used to define the location of a key store in an archive. For any other
  repository the annex remote UUID is taken. This feature further aids the handling
  of large numbers of repositories in a backup or data store use case, because
  locations are derived from repository properties rather than having to re-configure
  them explicitly.


## Installation

Before you install this package, please make sure that you [install a recent
version of git-annex](https://git-annex.branchable.com/install).  This special
remote requires at minimum git-annex version 6.20160511. Afterwards,
install the latest version of `git-annex-ria-remote` from
[PyPi](https://pypi.org/project/git-annex-ria-remote):

    # install from PyPi
    pip install git-annex-ria-remote


## Use

A `ria` special remote is set up like any other "external"-type remote via the
git-annex `initremote` command. There is a single additional required argument
in contrast to the standard set: `base-path` which determines the base
directory where the special remote places its keys:

    git annex initremote myremote \
        type=external encryption=none \
        externaltype=ria base-path=/tmp/basepath/here

The remote is now ready for use. Any directories will be created on demand.
The key store for repository will be located underneath the given base path,
in a structure like this:

    /tmp/basepath/here
    └── 2e5
        └── 24934-a09e-11e9-8503-f0d5bf7b5561
            └── ff4
                └── c57
                    └── MD5E-s4--ba1f2511fc30423bdbb183fe33f3dd0f
                        └── MD5E-s4--ba1f2511fc30423bdbb183fe33f3dd0f

where the first two levels represent a tree structure that can host key stores
for any number of repositories, and the remaining level are identical to
the organization of a `directory`-type git-annex special remote.
The directory names for the two top-most levels are build from the git-annex
UUID for the special remote, or a DataLad dataset UUID, if available.

The special remote also supports SSH-based operation. To enable it, an
additional host name argument has to be given:

    git annex initremote myremote \
        type=external encryption=none \
        externaltype=ria base-path=/tmp/basepath/here \
        ssh-host=ria.example.com

This configuration will make the special remote use `/tmp/basepath/here` on
`ria.example.com`. Any SSH-access customizations (user name, ports, etc.) have
to be implemented via the standard SSH configuration mechanism, for example, by
placing a snippet like this in `$HOME/.ssh/config`:

    Host ria.example.com
      User mike
      Port 2222
      PreferredAuthentications publickey


## Support

All bugs, concerns and enhancement requests for this software can be submitted here:
https://github.com/datalad/git-annex-ria-remote/issues
