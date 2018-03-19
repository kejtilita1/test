import os
import subprocess
import sys
import argparse

from scmlib.errors import ScmError
from bambooci.exception import PassThroughException
from bambooci import utils

logger = utils.get_logger("branchPromotion")

def main(expected_source_branch_head_hash, 
		source_branch, 
		target_branch):
	git = utils.get_git_scm()
	
	git.gotoBranch(source_branch)
	git.updateAndMerge()
	
	current_head_hash = git.getCurrentRevision()
	if current_head_hash != expected_source_branch_head_hash:
		logger.error("Commits pushed to BitBucket while promoting one or more commits to branch {} is prohibited.".format(target_branch))
		raise PassThroughException()
	
	
	git.gotoBranch(target_branch)
	
	logger.info("Pulling latest commits for branch {}...".format(target_branch))
	
	git.updateAndMerge()
	
	merge_msg = 'Merge branch "{}" into "{}" for commit: {}'.format(source_branch, 
																target_branch, 
																expected_source_branch_head_hash)
	
	logger.info("Merging branch {} into {}...".format(source_branch, target_branch))
	
	try:
		git.runRawCommand(['merge', '--no-ff', '-m', merge_msg, source_branch])
	except ScmError, e:
		logger.error("Conflict encountered when merging branch {} into {}.  Need to resolve conflict(s) locally, push changes to BitBucket, and restart the promotion process.".format(source_branch, target_branch))
		raise PassThroughException()
	
	logger.info("The branches have been successfully merged.  Pushing merge result to BitBucket...")
	
	try:
		git.push()
	except ScmError, e:
		logger.error("The following unexpected error occurred while pushing the merge commit to BitBucket:\n{}".format(e.msg))
		raise PassThroughException()
	
	logger.info("Completed pushing merge result to BitBucket.  Exiting.")
	
	
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Merge/rebase from indicated branch to current branch')
	parser.add_argument('--hash', required=True, help='expected source branch head commit hash')
	parser.add_argument('--source', required=True, help='merge from this source branch')
	parser.add_argument('--target', default='integration', help='merge from source to target')
	
	args = parser.parse_known_args()[0]

	exit_code = 1
	try:
		main(args.hash, args.source, args.target)
		exit_code = 0
	except PassThroughException:
		pass
	
	sys.exit(exit_code)