'''
Created on Oct 25, 2017

@author: nseden
'''
import requests
import logging
import sys
import os
from argparse import ArgumentParser

STATUS_CODE_OK = 200
STATUS_CODE_BAD_REQUEST = 400

CMD_SUBMODULE_HASH_VALID = "submodvalid"
CMD_BRANCH_ALREADY_MERGED = "merged"

logger = logging.getLogger()

class LoggerThresholdRangeFilter(object):
    '''
    Custom filter used for displaying a range of logger level to a particular handler.
    '''
    def __init__(self, min_level, max_level):
        self.__min_level = min_level
        self.__max_level = max_level

    def filter(self, logRecord):
        return (logRecord.levelno <= self.__max_level and logRecord.levelno >= self.__min_level)

class MiscGitCmds(object):
    
    REST_API_ENDPOINT_PREFIX_PATH = "rest/miscgitcmds/1.0"
    
    def __init__(self, bitbucket_user, bitbucket_password, bitbucket_server="https://nsg-bit.intel.com", root_ca_certificate=False):
        self.bitbucket_user = bitbucket_user
        self.bitbucket_password = bitbucket_password
        self.bitbucket_server = bitbucket_server.rstrip("/")
        self.root_ca_certificate = root_ca_certificate
        
    def submodule_hash_valid(self,
             bitbucket_project_slug,
             bitbucket_repo_slug,
             commit_hash,
             submodule_project_slug,
             submodule_repo_slug,
             submodule_dir_path,
             submodule_valid_branches):
    
        params = dict()
        params['project'] = bitbucket_project_slug
        params['repo'] = bitbucket_repo_slug
        params['commitHash'] = commit_hash
        params['subProject'] = submodule_project_slug
        params['subRepo'] = submodule_repo_slug
        params['subDirPath'] = submodule_dir_path
        params['subValidBranches'] = submodule_valid_branches
                
        return self.__get("submoduleBranchHasCommit", params)['response']
        
    def branch_already_merged(self,
                              bitbucket_project_slug,
                              bitbucket_repo_slug,
                              source_branch,
                              target_branch):
    
        params = dict()
        params['project'] = bitbucket_project_slug
        params['repo'] = bitbucket_repo_slug
        params['sourceBranch'] = source_branch
        params['targetBranch'] = target_branch
        
        return self.__get("branchMerged", params)['response']
        
    
    def __get(self, url_endpoint, params):
        response = requests.get("{}/{}/{}".format(self.bitbucket_server,
                                                  self.REST_API_ENDPOINT_PREFIX_PATH,
                                                  url_endpoint.lstrip("/")),
                                params=params,
                                auth=(self.bitbucket_user, self.bitbucket_password), 
                                verify=self.root_ca_certificate)
        
        if response.status_code == STATUS_CODE_OK:
            return response.json()
        elif response.status_code == STATUS_CODE_BAD_REQUEST:
            # Client caused error, display response.
            logger.error(response.text)
            response.raise_for_status()
        else:
            # Server-side error
            logger.error("The server {} returned an error code indicating a server side error.  Please contact a system administrator if this error persists.".format(self.bitbucket_server))
            response.raise_for_status()
            
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    streamHandler = logging.StreamHandler(sys.stdout)
    streamHandler.setLevel(logging.INFO)
    streamHandler.addFilter(LoggerThresholdRangeFilter(logging.INFO, logging.INFO))
    streamHandler.setFormatter(logging.Formatter(fmt='%(levelname)s: %(message)s'))
    
    errorHandler = logging.StreamHandler(sys.stderr)
    errorHandler.setLevel(logging.ERROR)
    errorHandler.addFilter(LoggerThresholdRangeFilter(logging.WARN, logging.ERROR))
    errorHandler.setFormatter(logging.Formatter(fmt='%(levelname)s: %(message)s'))
    
    logger.handlers = []
    logger.addHandler(streamHandler)
    logger.addHandler(errorHandler)
    
    # Disable info logging.
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    
    parser = ArgumentParser()
    parser.add_argument("-server", dest='server', required=False, default="https://nsg-bit.intel.com", type=str, help="The Bitbucket server to run the script against.")
    parser.add_argument("-user", dest='user', required=True, type=str, help="Bitbucket user account.")
    parser.add_argument("-password", dest='password', required=True, type=str, help="Bitbucket user pass.")
    
    subparsers = parser.add_subparsers(dest='command')
    
    submodule_hash_valid_parser = subparsers.add_parser(CMD_SUBMODULE_HASH_VALID)
    submodule_hash_valid_parser.add_argument("-project", dest='project', required=True, type=str, help="The Bitbucket project SLUG.")
    submodule_hash_valid_parser.add_argument("-repo", dest='repo', required=True, type=str, help="The Bitbucket repo SLUG.")
    submodule_hash_valid_parser.add_argument("-commit", dest='commit_hash', required=True, type=str, help="The commit hash to verify the submodule link against.")
    submodule_hash_valid_parser.add_argument("-subProject", dest='subProject', required=True, type=str, help="The Bitbucket submodule project SLUG.")
    submodule_hash_valid_parser.add_argument("-subRepo", dest='subRepo', required=True, type=str, help="The Bitbucket submodule repo SLUG.")
    submodule_hash_valid_parser.add_argument("-subPath", dest='subPath', required=True, type=str, help="The relative path (from parent repo root) to the submodule mount point.")
    submodule_hash_valid_parser.add_argument("-branch", dest='branch', required=True, type=str, nargs='*', help="List of valid branches the submodule hash should exist on.")
    
    branch_merged_parser = subparsers.add_parser(CMD_BRANCH_ALREADY_MERGED)
    
    branch_merged_parser.add_argument("-project", dest='project', required=True, type=str, help="The Bitbucket project SLUG.")
    branch_merged_parser.add_argument("-repo", dest='repo', required=True, type=str, help="The Bitbucket repo SLUG.")
    branch_merged_parser.add_argument("-source", dest='source', required=True, type=str, help="The source branch being merged.")
    branch_merged_parser.add_argument("-target", dest='target', required=True, type=str, help="The target branch being merged into.")
    
    args = parser.parse_args()
    
    # SSL certificate should be inline with this script.
    path_to_script_dir = os.path.dirname(os.path.realpath(__file__))
    cert_file = os.path.join(path_to_script_dir, "IntelSHA256RootCA-Base64.crt")
    if not os.path.isfile(cert_file):
        raise Exception("The expected root certificate file {} does not exist.".format(cert_file))
    
    misc_cmds = MiscGitCmds(args.user, args.password, args.server, cert_file)
    
    exit_code = 0
    if args.command == CMD_SUBMODULE_HASH_VALID:
        if not misc_cmds.submodule_hash_valid(args.project, 
                                              args.repo, 
                                              args.commit_hash, 
                                              args.subProject, 
                                              args.subRepo, 
                                              args.subPath, 
                                              args.branch):
            logger.error("The submodule hash for submodule link {} does not exist on one of the following submodule GIT repository branches: {}".format(args.subPath,
                                                                                                                                                        ", ".join(args.branch))) 
            exit_code = 1                                                                                                                                            
    elif args.command == CMD_BRANCH_ALREADY_MERGED:
        if misc_cmds.branch_already_merged(args.project, 
                                           args.repo, 
                                           args.source, 
                                           args.target):
            logger.error("The source branch '{}' has already been merged into '{}'.".format(args.source, args.target))
            exit_code = 1
            
    sys.exit(exit_code)