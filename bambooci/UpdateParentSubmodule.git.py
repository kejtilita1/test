import os
import subprocess
import sys
import argparse
import error

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ARGUMENTS
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
parser = argparse.ArgumentParser(description='Script used to update the parent repo to point to the latest submodule changeset. Updating the target branch as indicated in the arguments passed in')
parser.add_argument('-t', '--target_branch', default='integration', help='Branch we wish to update in the parent repo to point to the latest commit in the submodule')
parser.add_argument('-s', '--source_branch', default='master', help='Subrepo source branch to pull from and update')
parser.add_argument('-p', '--path', default='src/transport', help='Relative path within the repo where the subrepo lives so that we can update it')
args = vars(parser.parse_args())

TARGET_BRANCH = args['target_branch']
SOURCE_BRANCH = args['source_branch']
PATH = args['path']
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# END ARGUMENTS
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#
# def GetCurrentCommit()
#
# Description: This method takes a command line as input, runs, executes and gets the return value (though we do nothing - 
# for now - with this return value)
#
# Assumptions: Runs on current working directory and it runs on a Windows host
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def GetCurrentCommit(path):
	
	command = "git -C " + path + " rev-parse HEAD"
	p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	for line in p.stdout.readlines():
		rev = line.decode('utf8').strip()	    
	retval = p.wait()
	return rev
	
#end RunCommand()
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
	    print ("DEBUG: " + line.decode('utf8').strip()),
	retval = p.wait()
	print ("Return value: " + str(retval))
	return retval
#end RunCommand()
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#
#	MAIN 
#
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#assume parent repo cloned with recursive flag

try:
	#need to set the user account otherwise it defaults to the Bamboo system account
	RunCommand("git config --local user.name sys_nsgciautomation")
	RunCommand("git config --local user.email sys_nsgCIAutomation@intel.com") 
	
	#checkout integration on parent repo to trigger CI flow to promote to master
	RunCommand ("git checkout " + TARGET_BRANCH)

	#git pull origin master on subrepo (-C flag indicates path to execute command) - this updates the subrepo to the latest commit
	RunCommand ("git -C " + PATH + " pull origin " + SOURCE_BRANCH)

	#Stage changes in the subrepo state to commit in the parent repo
	RunCommand ("git add " + PATH)
	
	#get the current revision/commit/hash from the subrepo after we update/pull from origin
	rev = GetCurrentCommit(PATH)	

	#Commit the changes locally - indicating what we updated and to what
	RunCommand ("git commit -m \"Updating transport subrepo to latest passing build in CI for " + PATH + " to commit [" + rev + "]\"")

	#push changes to server so that it updates for future clones
	retval = RunCommand ("git push")		

	if (retval == 0):	
			print ("SOLID!!!")			
	else:		
		print ("Unable to update parent repo to latest subrepo changes")
		os._exit(retval)
except:
	print ("DEBUG - something went wrong updating the parent repo")
	error.PrintError()
