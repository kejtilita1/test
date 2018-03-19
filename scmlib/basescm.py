from abc import ABCMeta
from abc import abstractmethod
import subprocess
import functools
import os
import datetime
import sys
import codecs

from .errors import ScmError
from .errors import ScmCommandError

#abstract class which other Scm classes will inherit from
class BaseScm(object):
    __metaclass__ = ABCMeta
    
    def __init__(self):
        self.localpath = None
        self.remotepath = None
        self.toolpath = None
        self.debug = False
        self.username = None
        self.password = None
        self.rawoutput = ""

    '''
    Decorator to indicate that the remote repo path is required before running. If the remote path is not specified, ScmError will be raised.
    '''
    @staticmethod
    def requiresRemoteRepo(f):
        @functools.wraps(f)
        def wrap(*args, **kwargs):
            self = args[0]
            if self.remotepath is None:
                raise ScmError("No remote SCM path specified.")
            return f(*args, **kwargs)
        return wrap

    '''
    Static scm function to find the given tool name in the users environment PATH.
    exeName is the name of the tool executable to find. e.g. hg.exe, git.exe, etc.
    Returns the full path of the tool if found, or None if not found
    '''    
    @staticmethod
    def findToolPath(exeName):
        for path in os.getenv('PATH').split(os.pathsep):
            path = path.strip("\"")
            toolpath = os.path.join(path, exeName)
            if os.path.exists(toolpath):
                return toolpath
        return None
        
    '''
    Set the debug state of this scm object to the given boolean value. If no value is specified, the current state will toggle.
    '''
    def setDebug(self, value=None):
        #toggle debug if no value is specified
        if value is None:
            value = not self.debug
        self.debug = bool(value)
        print("Debugging printing is {0}".format(self.debug))
        
    '''
    Print the given debug message to the screen. Only prints if the current debug state of the scm object is set to True. (see setDebug function)
    '''
    def debugPrint(self, msg):
        if self.debug:
            print(msg)

    '''
    Execute the the underlying SCM tool with the given argument list. If specified, will use 'cwd' as
    the directory to execute from. Executes from the local repo path by default.
    Returns the text output from the command on success.
    Raises ScmError with the failing output message along with the failing command (if applicable) if the command does not succeed.
    '''
    def _processScmCommand(self, args, cwd=None, outfile=None):
        if not isinstance(args, list):
            raise ScmError("Arguments to SCM tool not specified as a list")
            
        #subprocess doesn't like other types. Make everything a string.
        strargs = [str(a) for a in args]

        #unless told otherwise, execute the command in the repo
        if cwd is None:
            cwd = self.localpath
            
        if self.toolpath is None:
            raise ScmError("Tool executable is not set. Cannot execute command.")
            
        cmd = [self.toolpath] + strargs
        self.debugPrint("running command {0}".format(" ".join(cmd)))
        self.debugPrint(cmd)
        scmprocess = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
        cout, cerr = scmprocess.communicate()

        #decode the program output, replacing characters which cannot be converted
        #without this, output is not compatible between python 3.x and python 2.7
        self.rawoutput = cout.decode('utf-8', 'replace')
        if not isinstance(self.rawoutput, str):
            self.rawoutput = self.rawoutput.encode('utf-8', 'replace')
        
        if scmprocess.returncode != 0:
            raise ScmCommandError(cerr.decode('utf-8', 'replace'), " ".join(cmd), scmprocess.returncode)

        #write command output to a file if requested (in utf-8)
        if outfile is not None:
            with codecs.open(outfile, mode='w', encoding='utf-8', errors='replace') as f:
                f.write(self.rawoutput.decode('utf-8'))

        return self.rawoutput
        
    '''
    Allows running a raw command through the inherited class
    '''
    def runRawCommand(self, arglist, cwd=None, outfile=None):
        return self._processScmCommand(arglist, cwd, outfile)
        
    '''
    Return the raw text output from the last command. Intended for debug only.
    '''
    def getRawOutput(self):
        return self.rawoutput

    '''
    Align a datetime object to the Monday of that work week.
    '''
    @staticmethod
    def alignTimestamp(dobj):
        truncated = dobj.replace(hour=0, minute=0, second=0, microsecond=0)
        aligned = (truncated - datetime.timedelta(days=truncated.isocalendar()[2]-1))
        return aligned

    '''
    Returns a string indiciating the scm type (i.e. "hg", "git", "dummy", etc.)
    '''
    @abstractmethod
    def scmType(self):
        pass

    '''
    Returns a string indiciating the main branch name (i.e. "default", "master", "dummy", etc.)
    '''
    @abstractmethod
    def getMainBranchName(self):
        pass

    '''
    Initialize a repo from scratch in the local path.
    Returns nothing on success. Raises ScmError on error.
    '''
    @abstractmethod
    def initialize(self):
        pass

    '''
    Clone a repo from the remote path into the local path.
    Returns nothing on success. Raises ScmError on error.
    '''
    @abstractmethod
    def clone(self):
        pass

    '''
    Add a file to be tracked by the repo. Also used to stage files for commit.
    If filename is specified, only add the given file. If no filename is specified, add all files.
    Returns nothing on success. Raises ScmError on error.
    '''
    @abstractmethod
    def addFile(self, filename=None):
        pass

    '''
    Commit changes to the repository.
    If message is specified, use the given commit message.
    Returns nothing on success. Raises ScmError on error.
    '''
    @abstractmethod
    def commit(self, message):
        pass
        
    '''
    Push changes to the remote repository. If underlying SCM does not support pushing, this is a no-op.
    Returns nothing on success. Raises ScmError on error.
    '''
    @abstractmethod
    def push(self):
        pass
        
    '''
    Return the current state of files in the repository.
    If type is specified ("modified", "added", "removed", "deleted", "unknown", "clean", "ignored"), only return status for the requested type.
    If type is not specified, will return status for all types.
    Returns a list of tuples for the requested file types on success. Raises ScmError on error. List can be empty if there are no modified files.
    '''
    @abstractmethod
    def status(self, type=None, include=None, exclude=None):
        pass
        
    '''
    Move the current pointer in the repository to the given revision id.
    Returns nothing on success. Raises ScmError on error.
    '''
    @abstractmethod
    def gotoRevision(self, revision=None):
        pass
        
    '''
    Returns the revision id for the currently pointed to revision in the repository
    Returns the current revision id on success. Raises ScmError on error.
    '''
    @abstractmethod
    def getCurrentRevision(self, showmod=False, length=None):
        pass
        
    '''
    Change to the requested branch name in the repository.
    Returns nothing on success. Raises ScmError on error.
    '''
    @abstractmethod
    def gotoBranch(self, branch):
        pass
        
    '''
    Return the name of the branch currently used in the repository.
    Returns the name of the current branch success. Raises ScmError on error.
    '''
    @abstractmethod
    def getCurrentBranch(self):
        pass
        
    '''
    Return a list of the local branches.
    '''
    @abstractmethod
    def getBranches(self):
        pass
        
    '''
    Create a branch with the given name at the current revision. does not switch to the new branch.
    '''
    @abstractmethod
    def createBranch(self, name):
        pass
        
    '''
    Get the latest changes from the remote repository, and change the current pointer to (merging if necessary) to the latest revision.
    Equivalent to 'git pull', or 'hg pull -u', etc
    Returns nothing on success. Raises ScmError on error.
    '''
    @abstractmethod
    def updateAndMerge(self):
        pass
        
    '''
    Get the latest changes from the remote repository, but do not change the current revision
    Equivalent to 'git fetch', or 'hg pull', etc
    Returns nothing on success. Raises ScmError on error.
    '''
    @abstractmethod
    def update(self):
        pass
        
    '''
    Merge the currently pointed to revision with the given revision id.
    Returns nothing on success. Raises ScmError on error.
    '''
    @abstractmethod
    def merge(self, revision):
        pass
        
    '''
    Get the patch output (diff) for the given revision id.
    if outfile is specified, write the patch text to the outfile path.
    Returns the text of the patch on success. Raises ScmError on error.
    
    NOTE: this function supports submodules since both mercurial and git support
          submodules/subrepos with the diff command in similar fashion. No need to iterate subrepos if
          calling this with submodules=True (default)
    '''
    @abstractmethod
    def getPatch(self, rev1=None, rev2=None, outfile=None, context=5, stat=False, include=None, exclude=None, submodules=True):
        pass
        
    '''
    Get log information for one or more revisions. Gets log data for all revisions by default.
    If revision is specified, get log data for only the specified revision.
    If limit is specified, only return at most <limit> log entries.
    Returns a list of dictionaries containing log data. Each dictionary contains the revision ('hash'),
    commiting user id ('idsid'), date of the change ('date'), and commit message ('message')
    Raises ScmError on error
    '''
    @abstractmethod
    def log(self, revision=None, limit=None, file=None, startdate=None, enddate=None):
        pass
        
    '''
    Get log information for the first-parent ancestor path of a revision.
    If revision is specified, get log data for only the specified revision.
    If limit is specified, only return at most <limit> log entries.
    Returns a list of dictionaries containing log data. Each dictionary contains the revision ('hash'),
    commiting user id ('idsid'), date of the change ('date'), and commit message ('message')
    Raises ScmError on error
    '''
    @abstractmethod
    def getAncestors(self, revision=None, limit=None):
        pass
        
    '''
    Returns a list of tags that have been committed, ordered from newest to oldest.
    Raises ScmError on error.
    '''
    @abstractmethod
    def getTags(self, filter=None):
        pass
        
    '''
    Add a tag with the given name and message to the currently pointed to revision id in the repository.
    Returns nothing on success. Raises ScmError on error.
    '''
    @abstractmethod
    def createTag(self, name, message):
        pass
        
    '''
    Returns a the name of the latest tag used
    Raises ScmError on error.
    '''
    @abstractmethod
    def getLatestTag(self):
        pass

    '''
    Returns a list of all the tracked files in the repository.
    Raises ScmError on error.
    '''
    @abstractmethod
    def getFiles(self):
        pass
        
    '''
    Revert changes to one or more files.
    If filename is specified, only revert changes to that file. If not specified (default) revert changes to all files.
    Returns nothing on success. Raises ScmError on error.
    '''
    @abstractmethod
    def revertFile(self, filename=None):
        pass
        
    '''
    Return a list of the subrepositories/submodules, if any. Returns an empty list if none.
    '''
    @abstractmethod
    def getSubrepos(self):
        pass
        
    '''
    Return a string with the remote URL as detected by the tool (could be different from self.remotepath)
    '''
    @abstractmethod
    def getRemote(self):
        pass

    '''
    Return a string indicating the local repo directory as detected by the tool (could be different from self.localpath)
    '''
    @abstractmethod
    def getLocal(self):
        pass

    '''
    Returns a dictionary containing parameters from the repository config. Each key is a config setting.
    Keys returned: username
    '''
    @abstractmethod
    def getConfig(self):
        pass

    '''
    Returns a list of tool version
    '''
    @abstractmethod
    def getToolVersion(self):
        pass
