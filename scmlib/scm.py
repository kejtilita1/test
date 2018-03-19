import os

from .git import GitScm
from .hg import HgScm
from .dummy import DummyScm
from .errors import ScmError

def ScmFactory(localpath, remotepath=None, user=None, pw=None):
    if os.path.exists(os.path.join(localpath, ".git")) and os.path.exists(os.path.join(localpath, ".hg")):
        #frankenrepo contains both hg and git info..
        raise ScmError("Repository at {0} contains both mercurial and git info.".format(localpath))
    if os.path.exists(os.path.join(localpath, ".git")) or (remotepath is not None and "nsg-bit" in remotepath):
        #must be a git repo
        return GitScm(localpath, remotepath, user, pw)
    if os.path.exists(os.path.join(localpath, ".hg", "hgrc")) or (remotepath is not None): #eventually we'll want to check for nsg-hg in the remotepath
        #must be a hg repo
        return HgScm(localpath, remotepath, user, pw)
    if localpath == "dummy":
        return DummyScm(r'c:\dummy')
        
    return None
