from .basescm import BaseScm
from .errors import ScmError

import re
import os
import datetime
import sys

class GitScm(BaseScm):
    def __init__(self, localrepo, remoterepo=None, username=None, password=None):
        if localrepo is None:
            raise ScmError("Local repository path {0} is not available".format(localrepo))
            
        super(GitScm, self).__init__()
        
        #try to pull the remote repo path from the local config if it's not specified
        if os.path.exists(os.path.join(localrepo, ".git", "config")) and remoterepo is None:
            try:
                with open(os.path.join(localrepo, ".git", "config"), "r") as file:
                    rex = re.compile(r"^\s*url\s*=\s*(.*)$")
                    for line in file:
                        m = rex.match(line)
                        if m:
                            remoterepo = m.group(1)
                            break
            except IOError:
                pass  # If we don't know remoterepo, we can still do some things, so this should not be a major failure

        #update the remote path with the username and password if specified
        if username and password and remoterepo:
            remoterepo = remoterepo.replace("://", "://%s:%s@" % (username, password), 1)

        self.debugPrint("initializing with {0} - {1}".format(localrepo, remoterepo))
        self.localpath = localrepo
        self.remotepath = remoterepo
        self.username = username
        self.password = password

        self.toolpath = BaseScm.findToolPath("git" + ('.exe' if sys.platform.startswith('win') else ''))
        if self.toolpath is None:
            raise ScmError("Cannot find git executable. Must have git available in your PATH to use commands")
        
    '''
    Private function to generate pathspec args based on include/exclude parameters
    '''
    def _getPathspecArgs(self, include=None, exclude=None):
        args = []
        if include or exclude:
            args.append("--")

        if include:
            args.extend([":(top){0}".format(x) for x in include])

        if exclude:
            args.extend([":(top,exclude){0}".format(x) for x in exclude])
            
        return args

    '''
    Returns a string indiciating the scm type (i.e. "hg", "git", "dummy", etc.)
    '''
    def scmType(self):
        return "git"
        
    '''
    Returns a string indiciating the main branch name (i.e. "default", "master", "dummy", etc.)
    '''
    def getMainBranchName(self):
        return "master"

    '''
    Initialize a repo from scratch in the local path.
    Returns nothing on success. Raises ScmError on error.
    '''
    def initialize(self):
        self._processScmCommand(['init'])

    '''
    Clone a repo from the remote path into the local path.
    Returns nothing on success. Raises ScmError on error.
    '''
    @BaseScm.requiresRemoteRepo
    def clone(self):
        self._processScmCommand(['clone', '--recurse', self.remotepath, self.localpath], cwd='.')

    '''
    Add a file to be tracked by the repo. Also used to stage files for commit.
    If filename is specified, only add the given file. If no filename is specified, add all files.
    Returns nothing on success. Raises ScmError on error.
    '''
    def addFile(self, filename=None):
        args = ['add']
        if filename is not None:
            if isinstance(filename, list):  #append a list of multiple files
                args.extend(filename)
            else:                           #append a single filename
                args.append(filename)
        else:
            args.append(".")
        self._processScmCommand(args)

    '''
    Commit changes to the repository.
    If message is specified, use the given commit message.
    Returns nothing on success. Raises ScmError on error.
    '''
    def commit(self, message):
        args = ['commit']
        if self.username:
            args.extend(['-u', self.username])
        args.extend(['-m', message])
        self._processScmCommand(args)
        
    '''
    Push changes to the remote repository. If underlying SCM does not support pushing, this is a no-op.
    Returns nothing on success. Raises ScmError on error.
    '''
    @BaseScm.requiresRemoteRepo
    def push(self):
        self._processScmCommand(['push', self.remotepath])
        self._processScmCommand(['push', '--tags', self.remotepath])
        
    '''
    Return the current state of files in the repository.
    If type is specified ("modified", "added", "removed", "deleted", "unknown", "clean", "ignored"), only return status for the requested type.
    If type is not specified, will return status for all types.
    Returns a list of tuples for the requested file types on success. Raises ScmError on error. List can be empty if there are no modified files.
    '''
    def status(self, type=None, include=None, exclude=None):
        typeLookup = {
            "modified": 'M',
            "added": 'A',
            "removed": 'D',
            "deleted": 'D',
        }
        
        stateLookup = {
            "M": "mod",
            "A": "add",
            "D": "del",
        }

        if type is not None:
            if not type in typeLookup:
                raise ScmError("Unknown file type to search for: {0}".format(type))

        args = ['status', '-s']
        
        args.extend(self._getPathspecArgs(include, exclude))

        output = self._processScmCommand(args)

        results = []
        for line in output.splitlines():
            line = line.strip()
            if len(line) > 0:
                line = line.split()
                #filter results based on type if needed
                if type is not None:
                    if typeLookup[type] == line[0]:
                        if line[0] in stateLookup:
                            state = stateLookup[line[0]]
                        else:
                            state = "unk"
                        results.append((state, line[1]))
                else:
                    if line[0] in stateLookup:
                        state = stateLookup[line[0]]
                    else:
                        state = "unk"
                    results.append((state, line[1]))
        return results
        
    '''
    Move the current pointer in the repository to the given revision id.
    Returns nothing on success. Raises ScmError on error.
    '''
    def gotoRevision(self, revision=None):
        if revision is None:
            revision = "master"
        self._processScmCommand(['checkout', revision])
        #update submodules to the current revision, if there are any
        if len(self.getSubrepos()) > 0:
            self._processScmCommand(['submodule', 'update'])
        
    '''
    Returns the revision id for the currently pointed to revision in the repository
    Returns the current revision id on success. Raises ScmError on error.
    '''
    def getCurrentRevision(self, showmod=False, length=None):
        output = self._processScmCommand(['rev-parse', 'HEAD'])

        lines = output.splitlines()
        rev = lines[0].strip()
        if len(rev) == 0:
            raise ScmError("Current revision not found")
            
        if length:
            rev = rev[:length]
        if showmod == True:
            #add ending "+" that mercurial adds if there are uncommitted changes locally
            output = self._processScmCommand(['describe', '--always', '--dirty'])
            if "-dirty" in output:
                rev = rev + "+"
        return rev
        
    '''
    Change to the requested branch name in the repository.
    Returns nothing on success. Raises ScmError on error.
    '''
    def gotoBranch(self, branch):
        #checkout a specific branch
        self.gotoRevision(branch)
        
    '''
    Return the name of the branch currently used in the repository.
    Returns the name of the current branch success. Raises ScmError on error.
    '''
    def getCurrentBranch(self):
        output = self._processScmCommand(['rev-parse', '--abbrev-ref', 'HEAD'])

        lines = output.splitlines()
        brname = lines[0].strip()
        if len(brname) == 0:
            raise ScmError("Current branch name not found")
        return brname
        
    '''
    Return a list of the local branches - does not return detached HEADs
    '''
    def getBranches(self):
        output = self._processScmCommand(['show-ref', '--heads'])
        lines = output.splitlines()
        refs = []
        for line in lines:
            if line.strip() == "":
                continue
            refs.append(line.strip().split()[1])

        branches = []
        for ref in refs:
            output = self._processScmCommand(['log', '-n', 1, ref])
            changesets = self._parseChangesets(output)
            changesets[0]['branch'] = ref[len("refs/heads/"):]
            branches.extend(changesets)
        return branches
        
    '''
    Create a branch with the given name at the current revision. does not switch to the new branch.
    '''
    def createBranch(self, name):
        self._processScmCommand(['branch', name])
            
    '''
    Get the latest changes from the remote repository, and change the current pointer to (merging if necessary) to the latest revision.
    Equivalent to 'git pull', or 'hg pull -u', etc
    Returns nothing on success. Raises ScmError on error.
    '''
    @BaseScm.requiresRemoteRepo
    def updateAndMerge(self):
        self._processScmCommand(['pull'])
        
    '''
    Get the latest changes from the remote repository, but do not change the current revision
    Equivalent to 'git fetch', or 'hg pull', etc
    Returns nothing on success. Raises ScmError on error.
    '''
    @BaseScm.requiresRemoteRepo
    def update(self):
        self._processScmCommand(['fetch'])
        
    '''
    Merge the currently pointed to revision with the given revision id.
    Returns nothing on success. Raises ScmError on error.
    '''
    def merge(self, revision):        
        self._processScmCommand(['merge', revision])
        
    '''
    Get the patch output (diff) for the given revision id.
    if outFile is specified, write the patch text to the outFile path.
    Returns the text of the patch on success. Raises ScmError on error.
    '''
    def getPatch(self, rev1=None, rev2=None, outfile=None, context=5, stat=False, include=None, exclude=None, submodules=True):
        args = ["diff"]
        if submodules:
            args.append("--submodule=diff")
        if not stat:
            #don't want to add this if a stat is requested, otherwise it will include diff output too
            args.append("-U{0}".format(context))
        if stat:
            #only want stat output, no diff output (mimic mercurial behavior)
            args.append("--stat=1000") # width 1000 to prevent path truncation 

        if not rev1:
            #all changes since HEAD (not committed)
            pass
        if rev1 and not rev2:
            #changes for a specific commit
            args.append("{0}^!".format(rev1))
        elif rev1 and rev2:
            #changes between 2 commits
            args.append("{0}..{1}".format(rev1, rev2))
            
        args.extend(self._getPathspecArgs(include, exclude))
        
        output = self._processScmCommand(args, outfile=outfile)
        return output

    '''
    Private function to parse the git log/changeset list output
    Returns a list of the changesets it parsed
    '''
    def _parseChangesets(self, output):
        changesets = []
        changeset = None
        for line in output.splitlines():
            line = line.rstrip()
            if line.startswith("commit "):
                #commit XXXXXXXXXXXXXXXX
                line = line[len("commit "):].strip()
                changeset = dict()
                ids = line.split()
                changeset['hash'] = ids[0]
                changeset['parents'] = []
                if len(ids) > 1:
                    changeset['parents'] = [p for p in ids if p != changeset['hash']]
                changesets.append(changeset)
            elif line.startswith("Author: "):
                #Author: idsid <idsid@domain>
                #Author: Last, First <idsid@domain>
                line = line[len("Author: "):]
                line = line.strip()
                splitline = splitline = line.split("<")
                changeset['idsid'] = splitline[0].strip()
            elif line.startswith("Date: "):
                #get ww/yr format from date
                dstr = line[len("Date: "):]
                dstr = dstr.strip()
                #Fri Nov 09 12:44:01 2012 -0700
                #remove the timezone because python datetime sucks at that...
                dstr = dstr[:-5]
                dstr = dstr.strip()
                dobj = datetime.datetime.strptime(dstr, "%a %b %d %H:%M:%S %Y")
                dobj_aligned = BaseScm.alignTimestamp(dobj)
                changeset['timestamp'] = str(dobj)
                changeset['date'] = dstr
                changeset['iso'] = dobj.isocalendar()
                changeset['ts_aligned'] = str(dobj_aligned)
                changeset['iso_aligned'] = dobj_aligned.isocalendar()
            else:
                #assume it's part of the commit message
                line = line.strip()
                if len(line) > 0:
                    changeset['message'] = line

        return changesets
        
    '''
    Get log information for one or more revisions. Gets log data for all revisions by default.
    If revision is specified, get log data for only the specified revision.
    If limit is specified, only return at most <limit> log entries.
    Returns a list of dictionaries containing log data. Each dictionary contains the revision ('hash'),
    commiting user id ('idsid'), date of the change ('date'), and commit message ('message')
    Raises ScmError on error
    '''
    def log(self, revision=None, limit=None, file=None, startdate=None, enddate=None):
        #return a list of dictionaries (changeset/author/timestamp/message) containing log info as requested
        #if revision is none, return changesets for all revisions
        #if limit is none return all changesets
        args = ['log', '--parents', '--format=medium']
        if revision is not None:
            limit = 1 #for a single revision, only show 1
            args.append(revision)
        if limit is not None:
            args.extend(['-n', limit])
        if startdate:
            args.extend(["--after", startdate])
        if enddate:
            args.extend(["--before", enddate])
        if file is not None:
            args.append(file)
        output = self._processScmCommand(args)
        return self._parseChangesets(output)
        
    '''
    Get log information for the first-parent ancestor path of a revision.
    If revision is specified, get log data for only the specified revision.
    If limit is specified, only return at most <limit> log entries.
    Returns a list of dictionaries containing log data. Each dictionary contains the revision ('hash'),
    commiting user id ('idsid'), date of the change ('date'), and commit message ('message')
    Raises ScmError on error
    '''
    def getAncestors(self, revision=None, limit=None):
        args = ['rev-list', '--parents', '--first-parent', '--format=medium']
        if limit is not None:
            args.extend(['-n', limit])
        if revision is None:
            revision = "HEAD"
        args.append(revision)
        output = self._processScmCommand(args)
        return self._parseChangesets(output)

    '''
    Returns a list of tags that have been committed, ordered from newest to oldest.
    Raises ScmError on error.
    '''
    def getTags(self, filter=None):
        args = ['tag', '-l', '--sort=-taggerdate']  # sort newest to oldest to match hg
        if filter is not None:
            args.append(filter)
        output = self._processScmCommand(args)

        tags = []
        for line in output.splitlines():
            line = line.strip()
            if len(line) > 0:
                tags.append(line)
        return tags
        
    '''
    Add a tag with the given name and message to the currently pointed to revision id in the repository.
    Returns nothing on success. Raises ScmError on error.
    '''
    def createTag(self, name, message):
        args = ['tag', name, '-f', '-m', message]
        self._processScmCommand(args)
        
    '''
    Returns a the name of the latest tag used
    Raises ScmError on error.
    '''
    def getLatestTag(self):
        output = self._processScmCommand(['describe', '--tags'])
        return output.strip()

    '''
    Returns a list of all the tracked files in the repository.
    Raises ScmError on error.
    '''
    def getFiles(self):
        output = self._processScmCommand(['ls-tree', '-r', '--name-only', '--full-tree', 'HEAD'])

        files = []
        for line in output.splitlines():
            line = line.strip()
            if len(line) > 0:
                files.append(line)

        return files
        
    '''
    Revert changes to one or more files.
    If filename is specified, only revert changes to that file. If not specified (default) revert changes to all files.
    Returns nothing on success. Raises ScmError on error.
    '''
    def revertFile(self, filename=None):
        #git reset --hard
        if filename is None:
            args = ['reset', '--hard', 'HEAD']
        else:
            args = ['checkout', '--', filename]
        self._processScmCommand(args)
        
    '''
    Return a list of the subrepositories/submodules, if any. Returns an empty list if none.
    '''
    def getSubrepos(self):
        subrepos = []
        subrepoFile = self.localpath + os.sep + ".gitmodules"
        if not os.path.exists(subrepoFile):
            return subrepos
            
        #parse the .gitmodules file and get the directories that need to be wiped
        with open(subrepoFile) as srf:
            for line in srf:
                line = line.strip()
                if line.startswith("path ="):
                    splitline = line.split("=")
                    subrepos.append(splitline[1].strip())

        return subrepos

    '''
    Return a string with the remote URL as detected by the tool (could be different from self.remotepath)
    '''
    def getRemote(self):
        output = self._processScmCommand(['remote', '-v'])
        remote = ""
        #brute force. does not consider other remotes besides origin. does not account for separate fetch/push remotes.
        for line in output.splitlines():
            if line.startswith("origin"):
                line = line[len("origin"):]
                parts = line.strip().split()
                remote = parts[0]
        return remote.strip()
    '''
    Return a string indicating the local repo directory as detected by the tool (could be different from self.localpath)
    '''
    def getLocal(self):
        output = self._processScmCommand(['rev-parse', '--show-toplevel'])
        # cygwin hack
        output = output.replace('/cygdrive/c', 'C:')
        return output.strip()

    '''
    Returns a dictionary containing parameters from the repository config. Each key is a config setting.
    Keys returned: username
    '''
    def getConfig(self):
        config = {}
        output = self._processScmCommand(["config", "--get", "user.name"])
        config['username'] = output.strip()
        return config
        
    '''
    Returns a list of tool version
    '''
    def getToolVersion(self):
        output = self._processScmCommand(["--version"])
        #git version X
        chunks = output.strip().split()
        #X (really X.Y.Z)
        rev = chunks[2].split(".")
        #return up to the first 3 parts of the revision
        if len(rev) > 3:
            del rev[3:]
        return [int(ver) for ver in rev]
        
