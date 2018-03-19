'''
Created on Feb 23, 2018

@author: nseden
'''
import os
import sys
import argparse

from scmlib.errors import ScmError
from bambooci.exception import PassThroughException
from bambooci import utils

logger = utils.get_logger("checkoutSubmoduleBranch")

def main(local_parent_repo_dir, parent_repo_commit_hash, parent_repo_url, submodule_mount_dir, submodule_commit_hash):
    if not os.path.isdir(local_parent_repo_dir):
        os.makedirs(local_parent_repo_dir)
    
    try:
        git = utils.get_git_scm(local_parent_repo_dir, remoterepo=parent_repo_url, config_init=False)
        logger.info("Cloning {}...".format(parent_repo_url))
        git.clone()
        
        logger.info("Checking out parent repository revision {}...".format(parent_repo_commit_hash))
        git.gotoRevision(parent_repo_commit_hash)
        
        if not os.path.isdir(submodule_mount_dir):
            logger.error("The expected submodule path {} does not exist.".format(submodule_mount_dir))
            raise PassThroughException()
        
        git = utils.get_git_scm(submodule_mount_dir)
        
        logger.info("Checking out revision {} for submodule directory {}...".format(submodule_commit_hash, submodule_mount_dir))
        git.gotoRevision(submodule_commit_hash)
    except ScmError, e:
        logger.error("The following unexpected exception occurred while checking out the submodule topic branch:\n{}".format(e.msg))
        raise PassThroughException()
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Clones a parent repository against a particular submodule topic branch hash.')
    parser.add_argument('--local_parent_repo', required=True, help='Full path to the parent repository.')
    parser.add_argument('--parent_repo_url', required=True, help='The clone URL of the parent repository.')
    parser.add_argument('--parent_commit_hash', required=True, help='The commit hash to checkout in the parent repository.')
    parser.add_argument('--local_submodule_path', required=True, help='Full path to the expected submodule mount within the parent repository.')
    parser.add_argument('--submodule_commit_hash', required=True, help='The commit hash to checkout in the mounted submodule.')
    
    args = parser.parse_known_args()[0]

    exit_code = 1
    try:
        main(args.local_parent_repo, 
             args.parent_commit_hash, 
             args.parent_repo_url, 
             args.local_submodule_path, 
             args.submodule_commit_hash)
        exit_code = 0
    except PassThroughException:
        pass
    
    sys.exit(exit_code)