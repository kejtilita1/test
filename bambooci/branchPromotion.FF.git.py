import os
import subprocess
import sys
import argparse
import error

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ARGUMENTS
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
parser = argparse.ArgumentParser(description='Merge/rebase from indicated branch to current branch')
parser.add_argument('--hash', required=True ,help='Commit hash to merge from')
parser.add_argument('--target', default='master', help='merge to target')
args = vars(parser.parse_args())

HASH = args['hash']
TARGET = args['target']
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# END ARGUMENTS
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#
# def RunCommand()
#
# Description: This method takes a command line as input, runs, executes and gets the return value (though we do nothing - 
# for now - with this return value)
#
# Assumptions: Runs on current working directory and it runs on a Windows host
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def RunCommand(command):

	print (command)
	p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	for line in p.stdout.readlines():
	    print ("DEBUG: " + line.decode('utf8')),
	retval = p.wait()
	print ("Return value: " + str(retval))
	return retval
#end RunCommand()
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#Assumption: clone exists checked out to current branch we want to perform a Fast-Forward merge from

#need to set the user account otherwise it defaults to the Bamboo system account
RunCommand("git config --local user.name sys_nsgciautomation")
RunCommand("git config --local user.email sys_nsgCIAutomation@intel.com")

#set because of self-signed certs
command = "git config --global http.sslVerify false"
retval = RunCommand(command)

#set because of self-signed certs
command = "git checkout " + TARGET
retval = RunCommand(command)

#attempt to merge from remote parent branch
command = "git merge " + HASH
retval = RunCommand(command)

#if we don't have any issues - push to the server
if (retval == 0):
	command = "git push"
	retval = RunCommand(command)

	#if there are still no issues - we're SOLID!!!
	if (retval == 0):
		print ("SOLID!!!")
		sys.exit(0)
	else:
		#oops something went wrong *sad face*
		print ("Unable to push changes - merge/promotion FAILED")
		error.PrintError()
		sys.exit(retval)		
else:
	#oops something went wrong *sad face - the sequel*
	print ("Conflict encountered when merging from " + HASH + ". Need to resolve conflict locally and push changes to the server")
	error.PrintError()
	sys.exit(retval)



