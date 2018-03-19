'''
Created on Mar 13, 2018

@author: nseden
'''

from bambooci import utils
from scmlib.errors import ScmError
from bambooci.exception import PassThroughException

logger = utils.get_logger("autocodepromote")

class AutoCodePromote(object):
    
    def __init__(self, local_git_repo, disable_lfs=False, promote_retry_count=3):
        self.local_git_repo = local_git_repo
        self.git = utils.get_git_scm(local_git_repo, config_init=True)
        self.promote_retry_count = promote_retry_count
        
        if disable_lfs:
            # Local command, not catching exceptions
            logger.info("Disabling LFS hooks...")
            self.git.runRawCommand(['lfs', 'uninstall'])
            
    def promote_change(self, onChangeSourceHandlerFunc, target_branch, commit_msg, ff_ancestor_branch=None, tmp_banch_prefix="tmp"):
        """
        Promotes a set of file modifications to the target branch with the option of additionally merging the change to a GIT fast-forward branch.
        
        :param onChangeSourceHandlerFunc: Functional handler that does the actual source code file modifications.
        :param target_branct: The GIT branch to promote the file changes too.
        :param commit_msg: The message to include in the GIT commit representing the file changes.
        
        :param ff_ancestor_branch: Optional parameter specifying an additional branch to promote the change too.  Used common in repositories that fast-forward
        from an integration branch to a stable\release branch.
        :param tmp_banch_prefix: Local name of branch used to do the actual file modifications on.
        
        """
        
        ff_ancestor_branch_set = False
        if ff_ancestor_branch is not None and len(ff_ancestor_branch.strip()) > 0:
            ff_ancestor_branch_set = True
        
        merge_successful = False
        for i in range(0, self.promote_retry_count):
            logger.info("Updating repository files attempt {}/{}".format((i+1), self.promote_retry_count))
            
            target_branch_merged = False
            ff_ancestor_branch_merged = False
            
            try:
                tmp_branch = "{}_{}".format(tmp_banch_prefix, i)
                
                # Pull latest changes from origin
                self.git.gotoBranch(target_branch)
                self.git.createBranch(tmp_branch)
                self.git.gotoBranch(tmp_branch)
            
                
                onChangeSourceHandlerFunc(self.local_git_repo)
                
                
                modfiles = self.git.status("modified")
                if len(modfiles) > 0:
                    self.git.addFile()
                    logger.info("Committing local revision update.")
                    self.git.commit(commit_msg)
                    logger.info("Local revision update committed.")
                    
                    commit_hash = self.git.getCurrentRevision()
                    
                    #merge back to target target_branch.
                    self.git.gotoBranch(target_branch)
                    self.git.updateAndMerge()  #to fix issues with merge conflicts when pushing to master
                    self.git.merge(tmp_branch)
                    target_branch_merged = True
                    
                    if ff_ancestor_branch_set:
                        #try to merge into git ff ancestor target_branch
                        self.git.gotoBranch(ff_ancestor_branch)
                        self.git.updateAndMerge()
                        self.git.merge(tmp_branch)
                        ff_ancestor_branch_merged = True
                    
                    if ff_ancestor_branch_set:
                        # Update/merge operations are atomic.  Either we update both, or we don't update at all.                
                        self.git.runRawCommand(["push", "--atomic", "origin", target_branch, ff_ancestor_branch])
                    else:
                        self.git.runRawCommand(["push", "--atomic", "origin", target_branch])
                        
                    merge_successful = True
                    
                else:
                    logger.error("The file changes completed by the handler did not result in any file modifications.  This may be expected behavior.")
                    raise PassThroughException()
                
                break
            except ScmError as e:
                logger.error("SCM exception caught: {}".format(e.msg))
                
                # Reset the integration branches back to original state.  
                # Both should either be updated or not updated together.
                if ff_ancestor_branch_merged:
                    self.git.gotoBranch(ff_ancestor_branch)
                    self.git.runRawCommand(["reset", "--hard", "HEAD~1"])
                    
                if target_branch_merged:
                    self.git.gotoBranch(target_branch)
                    self.git.runRawCommand(["reset", "--hard", "HEAD~1"])
            
            if not merge_successful:
                raise Exception()
            
            return commit_hash