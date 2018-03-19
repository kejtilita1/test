import requests
import json
import sys
import os
import argparse
import error
 
################################################################################################################################################################################################
#
# Intel Corp - Copyright 2016
#
# Author: Rick Contreras
#
# Description: This script is used to automate the branch promotion from the indicated source branch to the target branch using the REST API for Bitbucket. This creates a Pull Request
# in the indicated project and repo - which then gets merged automatically - creating a non-fast-forward merge, e.g. a commit node on the target branch
#
################################################################################################################################################################################################

#===============================================================================================================================================================================================
# ARGS
#===============================================================================================================================================================================================
parser = argparse.ArgumentParser(description='Program used to promote/merge changes from a source branch to a target branch using Bitbucket REST API')
parser.add_argument('-s', '--source_branch', required=True, help='Source branch to merge from')
parser.add_argument('-t', '--target_branch', required=True, help='Target branch to merge to')
parser.add_argument('-r', '--repo', required=True, help='Git repo name')
parser.add_argument('-p', '--proj', required=True, help='Bitbucket project slug')
parser.add_argument('-u', '--user', required=True, help='Git user with access to repo')
parser.add_argument('--pswd', required=True, help='Git user password with access to repo')
parser.add_argument('-n', '--build_num', default='0', help='Optional build number')
parser.add_argument('-e', '--env', default='DEV', help="Environment we are running in, e.g. DEV or PROD")
args = vars(parser.parse_args())

CURRENT_BRANCH = args['source_branch']
TARGET_BRANCH = args['target_branch']
GIT_REPO = args['repo']
PROJECT = args['proj']
BUILD_NUMBER = args['build_num']
GIT_USER = args['user']
GIT_PASSWORD = args['pswd']
ENV = args['env']
GIT_REPO = GIT_REPO.lower()
POST_PULL_REQUEST = "https://nsg-bit-dev.intel.com/rest/api/1.0/projects/" + PROJECT + "/repos/" + GIT_REPO + "/pull-requests"

if ENV == "PROD":
	POST_PULL_REQUEST = "https://nsg-bit.intel.com/rest/api/1.0/projects/" + PROJECT + "/repos/" + GIT_REPO + "/pull-requests"
	
HEADERS = {'Content-type': 'application/json'}
#===============================================================================================================================================================================================
# End ARGS
#===============================================================================================================================================================================================

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#
# def merge
#
# Description: used to execute the merging from source to target branch in Bitbucket
#
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def merge(SOURCE_BRANCH, TARGET_BRANCH):

	#build our json string that we will use to post to the REST API endpoint to generate a pull request in Bitbucket
	json_data_to_create_pull_request = """{
		\"title\": \"Test Title\",
		\"description\": \"Test Description\",
		\"state\": \"OPEN\",
		\"open\": true,
		\"closed\": false,
		\"fromRef\": {
			\"id\": \"refs/heads/""" + SOURCE_BRANCH + """\",
			\"repository\": {
			\"slug\": \"""" + GIT_REPO + """\",
			\"name\": null,
			\"project\": {
				\"key\": \"""" + PROJECT + """\"
			}
		}
	},
	\"toRef\": {
		\"id\": \"refs/heads/""" + TARGET_BRANCH + """\",
		\"repository\": {
			\"slug\": \"""" + GIT_REPO + """\",
			\"name\": null,
			\"project\": {
				\"key\": \"""" + PROJECT + """\"
			}
		}
	},
	\"locked\": false,
	\"reviewers\": [],
	\"links\": {
			\"self\": [
				null
			]
		}
	}
	"""
	#end of json_data_to_create_pull_request definition
	
	print (json_data_to_create_pull_request)
	print (POST_PULL_REQUEST)

	#disable warnings - this is due to self-signed certificates
	requests.packages.urllib3.disable_warnings()

	try:
		#let's create our pull request
		response = requests.post(POST_PULL_REQUEST, data=json_data_to_create_pull_request, headers=HEADERS , auth=(GIT_USER, GIT_PASSWORD), verify=False)

		#and get the response in json format
		json_data = response.json() 

		#let's see the response code from the post request
		print ("SERVER response: " + str(response.status_code))		

		#check if we have errors if so, exit otherwise, continue - we expect 201 code from the above call
		if response.status_code != 201:
			#if there was a conflict - let's check if it's an actual conflict or the target is already up to date
			if response.status_code == 409:				
				print (json_data['errors'][0]['message'])
				#check the error message
				if "already up-to-date" in json_data['errors'][0]['message']:
					#nothing to do if branch is already up to date
					os._exit(0)
				else:
					raise
			else:
				raise
		
		#if we succeeded, we should get a pull request id
		id = json_data["id"]		
		
		print ("Version: " + str(json_data["version"]))

		#set the pull request value to merge to initiate our merge request
		json_data["state"] = "MERGED"		

		#convert the json_data to string
		d = json.dumps(json_data)
		print (str(d))		

		#post the data to complete the merge
		response = requests.post(POST_PULL_REQUEST + "/" + str(id) + "/merge", data=d, headers=HEADERS , auth=(GIT_USER, GIT_PASSWORD), verify=False)
		print ("Server response 2: " + str(response.status_code))
		
		if response.status_code == 409:
			json_data["version"] = "2"
			d = json.dumps(json_data)
			
			#try again with this new version setting
			response = requests.post(POST_PULL_REQUEST + "/" + str(id) + "/merge", data=d, headers=HEADERS , auth=(GIT_USER, GIT_PASSWORD), verify=False)
			
		json_data = response.json()

		#print confirmation showing merged
		print(json_data["state"])
		
	except: 		
		print ("DEBUG - Unable to merge from " + SOURCE_BRANCH + " to " + TARGET_BRANCH)
		raise

#end of def merge
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# MAIN
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def main():
	try:
		if CURRENT_BRANCH != "master":
			merge(CURRENT_BRANCH, TARGET_BRANCH)	
		#end if CURRENT_BRANCH != "master":	
	except:
		print ("DEBUG - Unable to perform merge")
		error.PrintError()
		sys.exit(1)
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# END MAIN
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__": main()

