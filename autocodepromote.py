'''
Created on Mar 13, 2018

@author: nseden
'''

from bambooci import utils
from scmlib.errors import ScmError

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

    def promote_change(self, onChangeSourceHandlerFunc, target_branch, commit_msg, ff_ancestor_branch=None, tmp_local_banch_name="tmp"):
        """
        Promotes a set of file modifications to the target branch with the option of additionally merging the change to a GIT fast-forward branch.

        WARNING: This code expects the file modifications to cause NO merge conflicts with the remote origin.  This code will fail ungracefully if
        multiple clients are pushing changes to the same files being modified by the handler function.

        :param onChangeSourceHandlerFunc: Functional handler that does the actual source code file modifications.
        :param target_branct: The GIT branch to promote the file changes too.
        :param commit_msg: The message to include in the GIT commit representing the file changes.

        :param ff_ancestor_branch: Optional parameter specifying an additional branch to promote the change too.  Used common in repositories that fast-forward
        from an integration branch to a stable\release branch.
        :param tmp_local_banch_name: Local name of branch used to do the actual file modifications on.

        """

        ff_ancestor_branch_set = False
        if ff_ancestor_branch is not None and len(ff_ancestor_branch.strip()) > 0:
            ff_ancestor_branch_set = True

        push_successful = False

        # Create temporary branch off the target branch.
        self.git.gotoBranch(target_branch)
        self.git.createBranch(tmp_local_banch_name)
        self.git.gotoBranch(tmp_local_banch_name)

        onChangeSourceHandlerFunc(self.local_git_repo)

        modfiles = self.git.status("modified")
        if len(modfiles) > 0:
            self.git.addFile()
            logger.info("Committing local file modifications...")
            self.git.commit(commit_msg)
            commit_hash = self.git.getCurrentRevision()

            #merge back to target target_branch.
            logger.info("Merging local file modifications to branch {}...".format(target_branch))
            self.git.gotoBranch(target_branch)
            self.git.merge(tmp_local_banch_name)
            if ff_ancestor_branch_set:
                logger.info("Merging local file modifications to branch {}...".format(ff_ancestor_branch))
                self.git.gotoBranch(ff_ancestor_branch)
                self.git.merge(tmp_local_banch_name)


            for i in range(0, self.promote_retry_count):
                try:
                    logger.info("Pulling target branches locally to pick up remote commits...")

                    # The file modifications should cause NO merge conflicts.
                    self.git.gotoBranch(target_branch)
                    self.git.updateAndMerge()
                    if ff_ancestor_branch_set:
                        self.git.gotoBranch(ff_ancestor_branch)
                        self.git.updateAndMerge()

                    logger.info("Pushing to remote origin attempt {}/{}...".format((i+1), self.promote_retry_count))

                    if ff_ancestor_branch_set:
                        # Update/merge operations are atomic.  Either we update both, or we don't update at all.
                        self.git.runRawCommand(["push", "--atomic", "origin", target_branch, ff_ancestor_branch])
                    else:
                        self.git.runRawCommand(["push", "--atomic", "origin", target_branch])

                    push_successful = True
                    logger.info("Remote origin push successful.")
                    break
                except ScmError as e:
                    logger.error("The following error was encountered while pushing the file modifications to remote origin: {}".format(e.msg))


        else:
            logger.error("The file changes completed by the handler did not result in any file modifications.  This is unexpected behavior.")
            raise Exception()

        if not push_successful:
            # Failed to push 3 times in a row.
            raise Exception()

        return commit_hash