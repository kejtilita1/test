'''
Created on Mar 1, 2018

@author: nseden
'''
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

logger = utils.get_logger("clone_git_repo")

def main(local_repo_path, repo_url, commit_hash):
    if not os.path.isdir(local_repo_path):
        os.makedirs(local_repo_path)
    
    try:
        git = utils.get_git_scm(local_repo_path, remoterepo=repo_url, config_init=False)
        logger.info("Cloning {}...".format(repo_url))
        git.clone()
        
        logger.info("Checking out repository revision {}...".format(commit_hash))
        git.gotoRevision(commit_hash)
    except ScmError, e:
        logger.error("The following unexpected exception occurred while cloning the repository:\n{}".format(e.msg))
        raise PassThroughException()
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Clones a GIT repository to a local directory and checks out the specified commit hash.')
    parser.add_argument('--local_repo_path', required=True, help='Local path where the repository should clone too.')
    parser.add_argument('--repo_url', required=True, help='The clone URL of the repository.')
    parser.add_argument('--commit_hash', required=False, help='The commit hash (or branch) to checkout.')
    
    args = parser.parse_known_args()[0]

    exit_code = 1
    try:
        main(args.local_repo_path, 
             args.repo_url, 
             args.commit_hash)
        exit_code = 0
    except PassThroughException:
        pass
    
    sys.exit(exit_code)