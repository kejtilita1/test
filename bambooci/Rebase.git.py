import os
import subprocess
import sys
import argparse
import logging
import io

from scmlib.errors import ScmError
from bambooci import utils
from bambooci.exception import PassThroughException

logger = utils.get_logger("rebase")

def main(source_branch):
	git = utils.get_git_scm()
	
	# Assumption is we are running this script in a local repository, with the target branch checked out.
	target_branch = git.getCurrentBranch()
	current_commit_hash = git.getCurrentRevision()
	
	try:
		#attempt to merge from remote parent branch
		pull_cmd_output = git.runRawCommand(['pull', '--no-ff', 'origin', source_branch])
	except ScmError, e:
		if 'Exiting because of an unresolved conflict.' in e.msg:
			logger.error("Conflict merging from integration to current branch. Need to resolve conflict locally and push changes to the server")
		else:
			logger.error("The following unexpected error occurred while merging branch {} into {}:\n{}".format(source_branch, target_branch, e.msg))
			
		raise PassThroughException()
			
	if 'Already up-to-date' in pull_cmd_output:
		logger.info("Branch {} is already up to date with {}.  Exiting.".format(target_branch, source_branch))
	else:
		current_commit_hash = git.getCurrentRevision() 
		logger.info("Branch {} has successfully merged with branch {}.  Pushing merge commit to origin...".format(target_branch, source_branch))
		
		try:
			git.runRawCommand(['push', 'origin', target_branch])
			logger.info("Successfully pushed commit to origin.")
		except ScmError, e:
			logger.error("The following unexpected exception occurred while pushing the merge commit to origin:\n{}".format(e.msg))
			
			raise PassThroughException()
		
	with io.open(os.path.join(os.path.abspath(os.getcwd()), "CommitHash.properties"), mode='w', encoding='ascii') as f:
		f.write(u"runCommitHash={}".format(current_commit_hash))

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Merge/rebase from indicated branch to current branch')
	parser.add_argument('-s', '--source_branch', default='integration', help='Source branch to rebase from')
	
	args = parser.parse_known_args()[0]
	
	exit_code = 1
	try:
		main(args.source_branch)
		exit_code = 0
	except PassThroughException:
		pass
	
	sys.exit(exit_code)