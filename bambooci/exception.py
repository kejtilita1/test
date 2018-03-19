'''
Created on Feb 10, 2018

@author: nseden
'''
class PassThroughException(Exception):
    '''
    Simple class to suggest information about the exception has already been printed. 
    '''
    def __init__(self):
        pass
