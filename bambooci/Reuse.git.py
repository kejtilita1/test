import requests
import json
import sys
import os
import subprocess
import zipfile
import io
import shutil
import argparse
import error

#####################################################################################################################################################################################################################
#
# Intel Corporation - Copyright 2016
#
# Author: Rick Contreras
#
# Description: Script used to determine if a binary already exists and downloads it instead of cloning the repo and building it. 
# This should save time because it doesn't have to clone the repository and it doesn't have to build the source code. First step 
# is to get the latest changeset in the current branch - we ignore merges and get the "real" commit ID for the actual change. 
# Merge commits, do not contain any actual changes and the way we store content in Artifactory, we use the commit ID for the 
# change. When it propagates up to the next branch, it has a Merge Commit followed by the original commit ID. The merge
# commit and the original commit are obviously different, so we can't use the tip of the branch, we need to scan for the latest 
# commit on the branch and then use that commit ID to attempt to download the artifacts. If they exist, we download them. If they 
# don't we default to cloning and building the source code.
#
#####################################################################################################################################################################################################################

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ARGUMENTS
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
parser = argparse.ArgumentParser(description='Detect if sources exist in Artifactory already. If so, download the artifacts, otherwise clone and build the code')
parser.add_argument('--git_user', required=True, help='Git user account to authenticate')
parser.add_argument('--git_pswd', required=True, help='Git user account password to authenticate')
parser.add_argument('--git_url', required=True, help='Git URL to clone from')
parser.add_argument('-p', '--git_project', default='ISE', help='Bitbucket Git project SLUG containing the repository')
parser.add_argument('--git_branch', default='master', help='Git branch we want to clone')
parser.add_argument('--git_repo', required=True, help='Git Repo name')
parser.add_argument('-b', '--build', required=True, help='Build command to execute if we can\'t retrieve artifacts from Artifactory')
parser.add_argument('-r', '--artifactory_relpath', required=True, help='Relative Artifactory path to store sources in')
parser.add_argument('--artifactory_user', required=True, help='Artifactory user account to authenticate')
parser.add_argument('--artifactory_pswd', required=True, help='Artifactory user account password to authenticate')
parser.add_argument('-s','--artifactory_url', default='https://ubit-artifactory-or.intel.com/artifactory/', help='Artifactory URL to use')
parser.add_argument('-o', '--out', default='C:\\temp', help='Location where binaries should be placed in')
parser.add_argument('-e', '--env', default='DEV', help='Environment, e.g. DEV or PROD to execute this script in')
args = vars(parser.parse_args())

GIT_USER = args['git_user']  #this is used for REST API call
GIT_PASSWORD = args['git_pswd'] #for the above account
GIT_URL = args['git_url'] #used for cloning if we are unable to reuse content from artifactory for some reason
PROJECT = args['git_project'] #this is used to pull commit IDs from BitBucket REST API
GIT_REPO = args['git_repo'] #repo name we are working on (for the above project)
CURRENT_BRANCH = args['git_branch'] #current branch we are executing on
BUILD_COMMAND = args['build'] #build command to run in case the artifacts needed don't exist
ARTIFACT_PATH = args['artifactory_relpath'] #relative artifact path in Artifactory
ARTIFACTORY_USER = args['artifactory_user'] #user login for artifactory
ARTIFACTORY_PSWD = args['artifactory_pswd'] # URL encoding friendly string for the above user
OUTPUT_PATH = args['out'] #we need to post the collateral from the retrieved artifacts in the network share for yet.py to consume
ENVIRONMENT = args['env'] #environment we are using (DEV or PROD)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# END ARGUMENTS
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# GLOBAL VARS
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
HEADERS = {'Content-type': 'application/json'} #used for REST API calls
BASE_BITBUCKET_URL = 'https://nsg-bit-dev.intel.com/rest/api/1.0/projects/'+PROJECT+'/repos/'+GIT_REPO+'/commits' #base bitbucket rest api URI
BASE_ARTIFACT_URL = 'http://' + ARTIFACTORY_USER + ':' + ARTIFACTORY_PSWD + '@ubit-artifactory-or.intel.com/artifactory/api/archive/download/' + ARTIFACT_PATH #base Artifactory URI to retrieve artifacts

if ENVIRONMENT == "PROD":
	BASE_BITBUCKET_URL = 'https://nsg-bit.intel.com/rest/api/1.0/projects/'+PROJECT+'/repos/'+GIT_REPO+'/commits' #base bitbucket rest api URI

if CURRENT_BRANCH != 'master':
	#set the bit bucket rest api URI accordingly (this filters out results by branch)
	BASE_BITBUCKET_URL = BASE_BITBUCKET_URL + "?until=refs%2Fheads%2F" + CURRENT_BRANCH

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# END GLOBAL VARS
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#
# def CleanDir()
#
# Description: This method takes no parameters and runs on the current working build directory as designated by Bamboo and 
# removes any contents in it to ensure we start with a clean working directory.
#
# Assumptions: Runs on current working directory and it runs on a Windows host
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def CleanDir():
	try:
		#remove contents of current folder
		for root, dirs, files in os.walk('.'):
			for f in files:
				os.unlink(os.path.join(root, f))
			for d in dirs:
				os.system('rmdir /S /Q \"{}\"'.format(d))
		#end for root, dirs, files in os.walk('.')
	except:		
		print ("DEBUG - unable to remove folder contents")
		raise

#end CleanDir()

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
	try:
		p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		for line in p.stdout.readlines():
			print ("DEBUG: " + line.decode( "utf8" ).strip()),
		retval = p.wait()
		return retval	
	except:
		print ("DEBUG - unable to execute command " + command)
		raise
#end RunCommand()

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#
# def Clone()
#
# Description: This method takes no parameters and performs a shallow clone of the branch and repo we need in order to checkout 
# and build the source code. We get to this point if we are unable to download artifacts from artifactory
#
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def Clone():

	try:
		print ("DEBUG - Cleaning Current Directory: " + os.getcwd())
		CleanDir()
	except:
		print ("DEBUG - cloning failed")
		raise

	try:
		#we'll do a shallow clone by creating a local repo - this is faster than cloning the entire thing
		print ("DEBUG - git init .")
		RunCommand("git init .")

		#we're gonna ignore self-signed certificates
		print ("DEBUG - git config --global http.sslVerify false")
		RunCommand("git config --global http.sslVerify false")
	
		#we pull what we need from the branch that we are working on
		print ("DEBUG - git pull --depth 1 " + GIT_URL + " " + CURRENT_BRANCH)
		RunCommand("git pull --depth 1 " + GIT_URL + " " + CURRENT_BRANCH)
	
		#we pull subrepos - bening if none exist
		print ("DEBUG - git submodule update --init")
		RunCommand("git submodule update --init")
	
	except:
		print ("DEBUG - cloning failed")
		raise

#end def Clone()

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#
# def Build()
#
# Description: Build command to build the source code
#
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def Build():	

	try:
		print ("DEBUG - " + BUILD_COMMAND)
		retval = RunCommand(BUILD_COMMAND)

		if retval != 0:
			os._exit(retval)
		
	except:
		print ("DEBUG - Unable to execute build command")
		raise

#end def Build()

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#
# def RetrieveURL(url, file_name)
#
# Description: This method will attempt to retrieve an artifact from the given URL and save it as "file_name" passed in as the second variable.
# If it fails, it returns false, otherwise, we return true
#
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def RetrieveURL(url):

	try:
		print ("DEBUG - attempting to retrieve artifacts")
		r = requests.get(url)

		if r.status_code == 200:		

			z = zipfile.ZipFile(io.BytesIO(r.content))
			z.extractall()

			#if we get this far - we're golden
			return True
			
		#end if rest.status_code == 200
	
	except:
		return False
	
	#if we're here something didn't go right
	return False
	
#end RetrieveURL(url)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#
# def AttemptArtifactRetrieval(artifact_id)
#
# Description: Attempt to retrieve the artifacts passed in as arguments to the script. We do this by using the artifact_id (e.g the commit ID) 
# and pull the contents into the local folder
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def AttemptArtifactRetrieval(artifact_id):

	#init our boolean to assume we haven't downloaded anything
	success = False

	try:
		print ("DEBUG: " + "Cleaning Dir")
		CleanDir()
	except:
		print("DEBUG - unable to clean current working directory")
		return False

	global BASE_ARTIFACT_URL

	if RetrieveURL(BASE_ARTIFACT_URL + artifact_id + "?archiveType=zip") == False:
		print ("DEBUG: " + "Artifact does not exist - will need to clone and build from scratch")
		return False

	#if we are here, means we successfully downloaded all the artifacts we needed	
	print ("DEBUG - Successfully retrieved ALL required artifacts")
	return True

#end def AttemptArtifactRetrieval()

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#
# def ExtractCommitID(commit_message)
#
# Description: Extracts the commit ID from the commit message - all commit messages resulting from a pull request follow the standard format of 'Merge pull request #<some unique numerical value> in <PROJ/Repo> from
# <source_branch> to <target_branch>\n\n* commit '<commit_id>':\n <commit_description>". We can extract the commit ID from this pull request by finding the line that contains the commit and extracting the substring
# containing the commit ID.
#
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def ExtractCommitID(commit_message):
	
	#init our boolean to assume we haven't downloaded anything
	commit_id = "null"
	
	commit_message_parts = commit_message.split("\n")
	for line in commit_message_parts:

		if "commit" in line:
			parts=line.split(':')
			if len(parts) == 2:
				commit_id = parts[1]					
			break	
			
	#return the commit_id
	return commit_id

#end def ExtractCommitID()
	
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#
# MAIN
# 
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def main():
	#assume we aren't re-using - better to err on the side of caution and just clone and build
	REUSE = False 

	#let's show which bitbucket server we're using
	print ("DEBUG - " + BASE_BITBUCKET_URL)

	try:
		#get commits via rest - if description contains merge and bitbucket admin
		response = requests.get(BASE_BITBUCKET_URL, headers=HEADERS, auth=(GIT_USER, GIT_PASSWORD), verify=False)	

		#parse the content into json form
		json = response.json() 
		
		#get the commit ID matching the current branch - only accepting merges done via Pull Requests through the automation, e.g. Bitbucket_admin
		for commit in json['values']:	

			if commit['message'].startswith('Merge branch') and commit['author']['name'] == "sys_nsgciautomation" and CURRENT_BRANCH in commit['message']: 

				#this has our commit id, let's extract it		
				commit_id = ExtractCommitID(commit['message'])

				print ("DEBUG - " + commit_id)

				#attempt to retrieve artifacts from artifactory
				REUSE = AttemptArtifactRetrieval(commit_id)	

				#we found the commit, so we can exit the loop	
				break

		print ("DEBUG - " + str(REUSE))

		#if we aren't re-using we'll have to build and clone
		if REUSE == False:
			print ("DEBUG - Cloning repo")
			Clone()

			print("DEBUG - Building code")
			Build()	
		else:
			#we have to move the contents we downloaded and extracted to the destination folder
			shutil.copytree(os.getcwd(), OUTPUT_PATH)		
		
	except:
		print ("DEBUG - unable to retrieve or build sources")
		error.PrintError()
		raise
		
if __name__ == "__main__": main()