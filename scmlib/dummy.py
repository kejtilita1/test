from .basescm import BaseScm
from .errors import ScmError

class DummyScm(BaseScm):
    '''
    A shell revision control system class for testing
    '''
    def __init__(self, localpath, remotepath=None):
        super(DummyScm, self).__init__()
        self.setDebug(True)
        self.debugPrint("initializing with {0} - {1}".format(localpath, remotepath))
        self.localpath = localpath
        self.remotepath = remotepath

    def scmType(self):
        return "dummy"
        
    def getMainBranchName(self):
        return "dummy"

    def initialize(self):
        self.debugPrint("Initializing repo")

    def clone(self):
        self.debugPrint("Cloning repo")

    def addFile(self, filename=None):
        self.debugPrint("Adding file {0}".format(filename))

    def commit(self, message=None):
        self.debugPrint("Committing to repo: {0}".format(message))
        
    def push(self):
        self.debugPrint("Pushing to repo")
        
    def status(self, type=None, include=None, exclude=None):
        self.debugPrint("Getting status")
        return []

    def gotoRevision(self, revision=None):
        self.debugPrint("Going to revision {0}".format(revision))

    def getCurrentRevision(self, showmod=False, length=None):
        revision = "dummyX"
        self.debugPrint("Getting revision {0}".format(revision))
        return revision
        
    def gotoBranch(self, branch):
        self.debugPrint("Moving to branch {0}".format(branch))
        
    def getCurrentBranch(self):
        branch = "dummyBranch"
        self.debugPrint("Getting branch {0}".format(branch))
        return branch
        
    def getBranches(self):
        self.debugPrint("Getting list of branches")
        return ["dummyBranch"]
        
    def getAncestors(self, revision=None, limit=None):
        self.debugPrint("Get ancestors of revision {0}".format(revision))
        return []

    def createBranch(self, name):
        self.debugPrint("Creating branch {0}".format(name))
        pass
        
    def updateAndMerge(self):
        self.debugPrint("Updating and merging")
        
    def update(self):
        self.debugPrint("Updating only")
        
    def merge(self, revision):
        self.debugPrint("Merging with revision {0}".format(revision))
        
    def getPatch(self, rev1=None, rev2=None, outfile=None, context=5, stat=False, include=None, exclude=None, submodules=True):
        self.debugPrint("Getting patch")
        return ""
        
    def log(self, revision=None, limit=None):
        self.debugPrint("Getting log for revision {0} with limit {1}".format(revision, limit))
        return []
        
    def getTags(self, filter=None):
        self.debugPrint("Getting tags for dummy repo")
        return []

    def createTag(self, name, message):
        self.debugPrint("Adding tag with name {0} and message {1}".format(name, message))

    def getLatestTag(self):
        self.debugPrint("Getting latest tag in repo")
        return []

    def getFiles(self):
        self.debugPrint("Getting list of all files in repo")
        return []
        
    def revertFile(self, filename=None):
        self.debugPrint("Reverting changes to files {0}".format(filename))
        
    def getSubrepos(self):
        return []
        
    def getRemote(self):
        return ""

    def getLocal(self):
        return ""

    def getConfig(self):
        return {}
        
    def getToolVersion(self):
        return [1,0,0]
