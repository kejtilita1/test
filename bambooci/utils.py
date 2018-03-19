'''
Created on Feb 8, 2018

@author: nseden
'''
import logging
import sys
import os

from scmlib import git

class LoggerThresholdRangeFilter(object):
    '''
    Custom filter used for displaying a range of logger level to a particular handler.
    '''
    def __init__(self, min_level, max_level):
        self.__min_level = min_level
        self.__max_level = max_level

    def filter(self, logRecord):
        return (logRecord.levelno <= self.__max_level and logRecord.levelno >= self.__min_level)


def get_logger(namespace):
    logger = logging.getLogger(namespace)
    logger.setLevel(logging.INFO)
    
    streamHandler = logging.StreamHandler(sys.stdout)
    streamHandler.setLevel(logging.INFO)
    streamHandler.addFilter(LoggerThresholdRangeFilter(logging.INFO, logging.INFO))
    streamHandler.setFormatter(logging.Formatter(fmt='%(levelname)s: %(message)s'))
    
    errorHandler = logging.StreamHandler(sys.stderr)
    errorHandler.setLevel(logging.WARN)
    errorHandler.addFilter(LoggerThresholdRangeFilter(logging.WARN, logging.ERROR))
    errorHandler.setFormatter(logging.Formatter(fmt='%(levelname)s: %(message)s'))
    
    logger.handlers = []
    logger.addHandler(streamHandler)
    logger.addHandler(errorHandler)
    
    return logger
    
    
def get_git_scm(local_repo_path=os.getcwd(), remoterepo=None, config_init=True):
    '''
    @return: git.GitScm
    '''
    ret_val = git.GitScm(local_repo_path, remoterepo=remoterepo)
    
    if config_init:
        ret_val.runRawCommand(['config', 'user.name', 'sys_nsgciautomation'])
        ret_val.runRawCommand(['config', 'user.email', 'sys_nsgCIAutomation@intel.com'])
    
    return ret_val
