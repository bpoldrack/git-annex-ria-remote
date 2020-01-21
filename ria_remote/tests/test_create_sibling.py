import os.path as op

from datalad.api import (
    Dataset,
    clone
)
from datalad.tests.utils import (
    with_tempfile,
    with_tree,
    assert_repo_status,
    assert_status,
    assert_in,
    assert_result_count,
    eq_,
    SkipTest,
    serve_path_via_http,
    assert_raises,
    chpwd
)

from datalad import cfg

from ria_remote.tests.utils import (
    skip_ssh,
)


@with_tempfile
def test_invalid_calls(path):

    ds = Dataset(path).create()

    # no argument:
    assert_raises(TypeError, ds.create_sibling_ria)

    # same name for git- and special remote:
    assert_raises(ValueError, ds.create_sibling_ria, 'ria+file:///some/where', name='some', ria_remote='some')

    # special remote not configured:
    res = ds.create_sibling_ria('ria+file:///some/where', name='some', return_type='list', on_failure="ignore")
    assert_result_count(res, 1,
                        status='impossible',
                        message="Missing required configuration 'annex.ria-remote.some-ria.base-path'")


@with_tree({'ds': {'file1.txt': 'some'},
            'sub': {'other.txt': 'other'}})
@with_tempfile
@with_tempfile(mkdir=True)
def _test_create_store(host, ds_path, base_path, clone_path):

    # TODO: This is an issue. We are writing to ~/.gitconfig here. Override doesn't work, since RIARemote itself
    #       (actually git-annex!) doesn't have access to it, so initremote will still fail.
    #       => at least move cfg.set/unset into a decorator, so it doesn't remain when a test is failing.
    cfg.set("annex.ria-remote.datastore-ria.base-path", base_path, where='global', reload=True)
    cfg.set("annex.ria-remote.datastore-ria.ssh-host", host or '0', where='global', reload=True)

    ds = Dataset(ds_path).create(force=True)
    subds = ds.create('sub', force=True)
    ds.save(recursive=True)
    assert_repo_status(ds.path)

    # don't specify special remote. By default should be git-remote + "-storage", which is what we configured
    res = ds.create_sibling_ria("ria+{prot}://{host}{base}".format(prot='ssh' if host else 'file',
                                                                   host=host if host else '',
                                                                   base=base_path),
                                "datastore")
    assert_result_count(res, 1, status='ok', action='create-sibling-ria')
    eq_(len(res), 1)

    # remotes exist, but only in super
    siblings = ds.siblings(result_renderer=None)
    eq_({'datastore', 'datastore-ria', 'here'}, {s['name'] for s in siblings})
    sub_siblings = subds.siblings(result_renderer=None)
    eq_({'here'}, {s['name'] for s in sub_siblings})

    # TODO: post-update hook was enabled

    # implicit test of success by ria-installing from store:
    ds.publish(to="datastore", transfer_data='all')
    with chpwd(clone_path):
        if host:
            clone('ria+ssh://{}{}#{}'.format(host, base_path, ds.id), path='test_install')
        else:
            # TODO: Whenever ria+file supports special remote config (label), change here:
            clone('ria+file://{}#{}'.format(base_path, ds.id), path='test_install')
        installed_ds = Dataset(op.join(clone_path, 'test_install'))
        assert installed_ds.is_installed()
        assert_repo_status(installed_ds.repo)
        eq_(installed_ds.id, ds.id)
        assert_in(op.join('ds', 'file1.txt'), installed_ds.repo.get_annexed_files())
        assert_result_count(installed_ds.get(op.join('ds', 'file1.txt')),
                            1,
                            status='ok', action='get', path=op.join(installed_ds.path, 'ds', 'file1.txt'))

    # now, again but recursive. force should deal with existing remotes in super
    res = ds.create_sibling_ria("ria+{prot}://{host}{base}".format(prot='ssh' if host else 'file',
                                                                   host=host if host else '',
                                                                   base=base_path),
                                "datastore",
                                recursive=True,
                                existing='replace')
    eq_(len(res), 2)
    assert_result_count(res, 2, status='ok', action="create-sibling-ria")

    # remotes now exist in super and sub
    siblings = ds.siblings(result_renderer=None)
    eq_({'datastore', 'datastore-ria', 'here'}, {s['name'] for s in siblings})
    sub_siblings = subds.siblings(result_renderer=None)
    eq_({'datastore', 'datastore-ria', 'here'}, {s['name'] for s in sub_siblings})

    cfg.unset("annex.ria-remote.datastore-ria.base-path", where='global', reload=True)
    cfg.unset("annex.ria-remote.datastore-ria.ssh-host", where='global', reload=True)


def test_create_simple():

    yield _test_create_store, None
    yield skip_ssh(_test_create_store), 'datalad-test'


# TODO: explicit naming of special remote
# TODO: Don't publish git history via --no-publish
# TODO: --no-server switch
