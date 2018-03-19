from .basescm import BaseScm
from .errors import ScmError

import re
import os
import datetime
import sys

class HgScm(BaseScm):
    '''
    A revision control system class for Mercurial.
    '''
    def __init__(self, localrepo, remoterepo=None, username=None, password=None):
        if localrepo is None:
            raise ScmError("Local repository path {0} is not available".format(localrepo))

        super(HgScm, self).__init__()

        #try to pull the remote repo path from the local config if it's not specified
        if os.path.exists(os.path.join(localrepo, ".hg", "hgrc")) and remoterepo is None:
            try:
                with open(os.path.join(localrepo, ".hg", "hgrc"), "r") as file:
                    rex = re.compile(r"^\s*default\s*=\s*(.*)$")
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

        self.toolpath = BaseScm.findToolPath("hg" + ('.exe' if sys.platform.startswith('win') else ''))
        if self.toolpath is None:
            raise ScmError("Cannot find hg executable. Must have mercurial available in your PATH to use commands")

    '''
    Private function to generate pathspec args based on include/exclude parameters
    '''
    def _getPathspecArgs(self, include=None, exclude=None):
        args = []
        if include:
            for i in include:
                args.append("-I")
                args.append("re:(?i){0}".format(i))

        if exclude:
            for x in exclude:
                args.append("-X")
                args.append("re:(?i){0}".format(x))

        return args

    '''
    Returns a string indiciating the scm type (i.e. "hg", "git", "dummy", etc.)
    '''
    def scmType(self):
        return "hg"

    '''
    Returns a string indiciating the main branch name (i.e. "default", "master", "dummy", etc.)
    '''
    def getMainBranchName(self):
        return "default"

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
        self._processScmCommand(['clone', self.remotepath, self.localpath], cwd='.')

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

    '''
    Return the current state of files in the repository.
    If type is specified ("modified", "added", "removed", "deleted", "unknown", "clean", "ignored"), only return status for the requested type.
    If type is not specified, will return status for all types.
    Returns a list of tuples for the requested file types on success. Raises ScmError on error. List can be empty if there are no modified files.
    '''
    def status(self, type=None, include=None, exclude=None):
        typeLookup = {
            "modified": '-m',
            "added": '-a',
            "removed": '-r',
            "deleted": '-d',
            "unknown": '-u',
            "clean": '-c',
            "ignored": '-i'
        }

        stateLookup = {
            "M": "mod",
            "A": "add",
            "D": "del",
            "R": "del",
            "I": "ign",
            "?": "unk",
            "C": "cln"
        }

        args = ['status']

        if type is not None:
            if not type in typeLookup:
                raise ScmError("Unknown file type to search for: {0}".format(type))
            args.append(typeLookup[type])
            
        args.extend(self._getPathspecArgs(include, exclude))

        output = self._processScmCommand(args)

        results = []
        for line in output.splitlines():
            line = line.strip()
            if len(line) > 0:
                line = line.split()
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
            revision = "default"
        self._processScmCommand(['update', '-r', revision])

    '''
    Returns the revision id for the currently pointed to revision in the repository
    Returns the current revision id on success. Raises ScmError on error.
    '''
    def getCurrentRevision(self, showmod=False, length=None):
        output = self._processScmCommand(['identify', '-i'])

        lines = output.splitlines()
        rev = lines[0].strip()
        if len(rev) == 0:
            raise ScmError("Current revision not found")

        if length:
            rev = rev[:length]
        if showmod == False:
            #strip off the ending "+" that mercurial adds if there are uncommitted changes locally
            rev = rev.rstrip("+")
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
        output = self._processScmCommand(['identify', '-b'])

        lines = output.splitlines()
        brname = lines[0].strip()
        if len(brname) == 0:
            raise ScmError("Current branch name not found")
        return brname

    '''
    Return a list of the local branches (named branches AND detached heads)
    '''
    def getBranches(self):
        #NOTE: if there are multiple heads, they will all have the same branch name (i.e. default)
        output = self._processScmCommand(['heads', '--debug', '--template', r'changeset: {rev}:{node}\nbranch: {branch}\nuser: {author}\ndate: {localdate(date, \'UTC\')|date}\nparents: {parents}\nsummary: {splitlines(desc) % \'{line} \'}\n\n'])
        return self._parseChangesets(output)

    @BaseScm.requiresRemoteRepo
    def updateAndMerge(self):
        self._processScmCommand(['pull', '-u'])

    @BaseScm.requiresRemoteRepo
    def update(self):
        self._processScmCommand(['pull'])

    def merge(self, revision):        
        self._processScmCommand(['merge', '-r', revision])

    def getPatch(self, rev1=None, rev2=None, outfile=None, context=5, stat=False, include=None, exclude=None, submodules=True):
        args = ["diff"]
        if submodules:
            args.append("-S")
        if not stat:
            #-U has no effect when stat is set, but we exclude it here anyway
            args.append("-U")
            args.append(context)
        if stat:
            args.append("--stat")

        if not rev1:
            #all changes since tip (not committed)
            pass
        if rev1 and not rev2:
            #changes for a specific commit
            args.extend(["-c", rev1])
        elif rev1 and rev2:
            #changes between 2 commits
            args.extend(["-r", rev1, "-r", rev2])
            
        args.extend(self._getPathspecArgs(include, exclude))
        
        output = self._processScmCommand(args, outfile=outfile)
        return output

    def log(self, revision=None, limit=None, file=None, startdate=None, enddate=None):
        #return a list of dictionaries (changeset/author/timestamp/message) containing log info as requested
        #if revision is none, return changesets for all revisions
        #if limit is none return all changesets
        args = ['log', '--debug', '--template', r'changeset: {rev}:{node}\nbranch: {branch}\nuser: {author}\ndate: {localdate(date, \'UTC\')|date}\nparents: {parents}\nsummary: {splitlines(desc) % \'{line} \'}\n\n']
        if revision is not None:
            limit = 1 #for a single revision, only show 1
            args.extend(['-r', revision])
        if limit is not None:
            args.extend(['-l', limit])
        if startdate and enddate:
            #date range
            args.extend(["--date", "{0} to {1}".format(startdate, enddate)])
        elif startdate:
            #single date
            args.extend(["date", startdate])
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
        args = ['log', '--debug', '--template', r'changeset: {rev}:{node}\nbranch: {branch}\nuser: {author}\ndate: {localdate(date, \'UTC\')|date}\nparents: {parents}\nsummary: {splitlines(desc) % \'{line} \'}\n\n', '-r', '"_firstancestors(.)"']
        if limit is not None:
            args.extend(['-n', limit])
        #need to modify the ancestors(.) to change rev...
        #if revision is None:
        #    revision = "tip"
        #args.append(revision)
        output = self._processScmCommand(args)
        return self._parseChangesets(output)
        
    '''
    Create a branch with the given name at the current revision. does not switch to the new branch.
    '''
    def createBranch(self, name):
        self._processScmCommand(['branch', name])
        
    '''
    Private function to parse the mercurial log/changeset list output
    Returns a list of the changesets it parsed
    '''
    def _parseChangesets(self, output):
        #parse the log messages into dictionaries..
        changesets = []
        changeset = None
        for line in output.splitlines():
            line = line.rstrip()
            if line.startswith("changeset:"):
                line = line[len("changeset:"):].strip()
                changeset = dict()
                splitline = line.split(":")
                changeset['id'] = splitline[0]
                changeset['hash'] = splitline[1]
                changeset['parents'] = []
                changesets.append(changeset)
            elif line.startswith("user:"):
                line = line[len("user:"):].strip()
                changeset['idsid'] = line
            elif line.startswith("parents:"):
                line = line[len("parents:"):].strip()
                parents = line.split()
                for parent in parents:
                    revs = parent.split(":")
                    if revs[0] != "-1":
                        changeset['parents'].append(revs[1])
            elif line.startswith("date:"):
                #get ww/yr format from date
                dstr = line[len("date:"):].strip()
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
            elif line.startswith("summary:"):
                msg = line[len("summary:"):].strip()
                changeset['message'] = msg
            elif line.startswith("branch:"):
                brname = line[len("branch:"):].strip()
                changeset['branch'] = brname
            else:
                pass

        self.debugPrint("num changesets={0}".format(len(changesets)))
        return changesets

    '''
    Returns a list of tags that have been committed, ordered from newest to oldest.
    Raises ScmError on error.
    '''
    def getTags(self, filter=None):
        #filter is non-functional since Hg does not support it
        output = self._processScmCommand(['tags'])

        tags = []
        for line in output.splitlines():
            m = re.match(r'^(.*?)\s*[0-9]+:[0-9a-f]+$', line)
            if m:
                tags.append(m.group(1))
        return tags

    '''
    Add a tag with the given name and message to the currently pointed to revision id in the repository.
    Returns nothing on success. Raises ScmError on error.
    '''
    def createTag(self, name, message):
        args = ['tag', name, '-f', '-m', message]
        if self.username:
            args.extend(['-u', self.username])
        self._processScmCommand(args)

    '''
    Returns a the name of the latest tag used
    Raises ScmError on error.
    '''
    def getLatestTag(self):
        output = self._processScmCommand(['log', '-r', '.', '--template', '"{latesttag}"'])
        return output.strip()

    '''
    Returns a list of all the tracked files in the repository.
    Raises ScmError on error.
    '''
    def getFiles(self):
        output = self._processScmCommand(['manifest'])

        files = []
        for line in output.splitlines():
            line = line.strip()
            if len(line) > 0:
                line = re.sub('^\d{1,3}\s{1,3}', "", line)
                files.append(line)

        return files

    '''
    Revert changes to one or more files.
    If filename is specified, only revert changes to that file. If not specified (default) revert changes to all files.
    Returns nothing on success. Raises ScmError on error.
    '''
    def revertFile(self, filename=None):
        args = ['revert']
        if filename is not None:
            args.append(filename)
        else:
            args.append('-a')
        self._processScmCommand(args)

    '''
    Return a list of the subrepositories/submodules, if any. Returns an empty list if none.
    '''
    def getSubrepos(self):
        subrepos = []
        subrepoFile = self.localpath + os.sep + ".hgsub"
        if not os.path.exists(subrepoFile):
            return subrepos
            
        #parse the .hgsub file and get the directories that need to be wiped
        with open(subrepoFile) as srf:
            for line in srf:
                # filter comments
                if not line.strip().startswith("#"):
                    splitline = line.split("=")
                    subrepos.append(splitline[0].strip())

        return subrepos

    '''
    Return a string with the remote URL as detected by the tool (could be different from self.remotepath)
    '''
    def getRemote(self):
        output = self._processScmCommand(['paths'])
        remote = ""
        #brute force. does not consider other remotes besides origin. does not account for separate fetch/push remotes.
        for line in output.splitlines():
            if line.startswith("default ="):
                parts = line.split("=")
                remote = parts[1]
        return remote.strip()

    '''
    Return a string indicating the local repo directory as detected by the tool (could be different from self.localpath)
    '''
    def getLocal(self):
        output = self._processScmCommand(['root'])
        return output.strip()
        
    '''
    Returns a dictionary containing parameters from the repository config. Each key is a config setting.
    Keys returned: username
    '''
    def getConfig(self):
        config = {}
        output = self._processScmCommand(["config"])
        match = re.search(r"ui.username *= *(.*)$", output, flags=re.IGNORECASE|re.MULTILINE)
        if(match):
            # Some Mercurial clients insist on adding the user's email address 
            # after the username, with whitespace in between. Truncate the username 
            # found through Mercurial at the first whitespace character.
            config['username'] = (match.group(1).split())[0]
        return config
        
    '''
    Returns a list of tool version
    '''
    def getToolVersion(self):
        output = self._processScmCommand(["version"])
        #Mercurial Distributed SCM (version X.Y.Z)
        m = re.search(r"version (\d+)\.(\d+)\.*(\d*)", output)
        if m:
            return [int(verNum) for verNum in m.groups()]
        return []
