'''
Created on Mar 13, 2018

@author: nseden
'''

import argparse
import sys

from scmlib.errors import ScmError
from bambooci import utils
from bambooci.exception import PassThroughException

PUSH_RETRY = 3
MODEL_FILE_PATH = "drive_detect.xml"

logger = utils.get_logger("commit_model_updates")

def main(local_git_repo, model_update_commit_msg, smi_files_update_commit_msg):
    try:
        git = utils.get_git_scm(local_git_repo)
        git.setDebug(True)
        should_push_changes = False
        
        # Required for passwordless pushes over SSH!
        git.runRawCommand(['lfs', 'uninstall'])
        
        git.addFile(MODEL_FILE_PATH)
        if len(git.status("modified")) > 0:
            git.commit(model_update_commit_msg)
            should_push_changes = True
        else:
            logger.info("No changes detected to file {}.".format(MODEL_FILE_PATH))
            
        git.addFile(r"data/SMI/\*.ini")
        git.addFile(r"data/SMI/\*.dat")
        if len(git.status("modified")) > 0:
            git.commit(smi_files_update_commit_msg)
            should_push_changes = True
        else:
            logger.info("No changes detected to SMI files.")
            
        if should_push_changes:
            push_success = False
            
            for i in range(0, PUSH_RETRY):
                try:
                    logger.info("Pushing model file and SMI file updates to origin attempt {}/{}".format((i+1), PUSH_RETRY))
                    # We expect no merge conflicts against the file this process updates.
                    git.updateAndMerge()
                    git.push()
                    push_success = True
                    break
                except ScmError as e:
                    logger.error("SCM exception caught: {}".format(e.msg))
                    
            if not push_success:
                raise PassThroughException()
            
            logger.info("Successfully pushed updated files to origin.  Exiting.")
    except ScmError as e:
        logger.error("SCM exception caught: {}".format(e))
        raise e
        
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Merge/rebase from indicated branch to current branch')
    parser.add_argument('--repo', required=True, help='Local path to the GIT repository.')
    parser.add_argument('--model_update_commit_msg', required=True, help='The message to include on the GIT commit.')
    parser.add_argument('--smi_files_update_commit_msg', required=True, help='The message to include on the GIT commit.')
    
    args = parser.parse_known_args()[0]
    
    exit_code = 1
    try:
        main(args.repo, args.model_update_commit_msg, args.smi_files_update_commit_msg)
        exit_code = 0
    except PassThroughException:
        pass
    
    sys.exit(exit_code)
