import requests
import sys
import os
import os.path
import zipfile
import io
import shutil
import argparse

#####################################################################################################################################################################################################################
#
# Intel Corporation - Copyright 2017
#
# Author: Rick Contreras
#
# Description: Script used to stash derived objects and build collateral into Artifactory. 
#
# Usage: python ArtifactoryPlugin.py -u user -p my_password -r ArtifactoryRepo/path/to/store/archive.zip -f C:\path\to\archive.zip -t D:\temp\path\to\save\zip\file
#
#	e.g. python ArtifactoryPlugin.py -u rcontre1 -p my_password -r NSG_fw-eng/CampbellHill/DEV/version/test/archive.zip -t D:\rcontre1\CI C:\temp
#
# 	NOTE: that the archive.zip doesn't generate a folder or file called archive.zip, it "explodes" the zip file to that location but you have to indicate the
#	archive.zip at the end of the path where you want to explode that zip file. It will retain the folder structure when it explodes it into Artifactory
#
#####################################################################################################################################################################################################################

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ARGUMENTS
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
parser = argparse.ArgumentParser(description='Program used to upload artifacts indicated to Artifactory')
parser.add_argument('-u', '--user', required=True, help='Artifactory user account to authenticate')
parser.add_argument('-p', '--pswd', required=True, help='Artifactory user account password to authenticate')
parser.add_argument('-r', '--relpath', required=True, help='Relative Artifactory path to store sources in')
parser.add_argument('-f', '--folder', required=True, help='Source folder containing artifacts to upload and store in Artifactory')
parser.add_argument('-t', '--tempdir', default='C:\\temp', help='Temporary directory to use to store a zip file generated by this script')
parser.add_argument('-s', '--server', default='https://ubit-artifactory-or.intel.com/artifactory/', help='Artifactory URL to use')
args = vars(parser.parse_args())

USER = args['user']  #authenticate with Artifactory server
PASSWORD = args['pswd'] #for the above
ARTIFACT_PATH = args['relpath'] #relative Artifactory path to upload contents
ARTIFACT_SOURCES = args['folder'] #local sources to upload, e.g. C\users\myfolder - would upload all contents from myfolder
ZIP_OUTPUT = args['tempdir'] #where we are storing the zip file temporarily to stage for upload
BASE_ARTIFACT_URL = args['server']
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# END ARGUMENTS
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# GLOBAL VARS
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
ZIP_FILE_NAME = "archive"
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# END GLOBAL VARS
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#
# def ZipFolder
# 
# Method to zip up files indicated in the folder_path parameter
#
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def Zipfolder(folder_path):
	try:		
		shutil.make_archive(ZIP_OUTPUT + "\\" + ZIP_FILE_NAME, 'zip', folder_path)
	except:
		raise 
#end Zipfolder

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#
# def CleanUp(path_to_file)
# 
# Method to remove file if it exists, otherwise does nothing
#
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def CleanUp (path_to_file):
	if os.path.exists(path_to_file):
		try:
			os.unlink(path_to_file)
		except:
			print ("DEBUG - Unable to remove zip file from " + path_to_file)
#end CleanUp

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#
# MAIN
# 
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def main():
	filename = ZIP_FILE_NAME + ".zip"
	localfilepath = os.path.abspath(os.path.join(ZIP_OUTPUT, filename))

	#relative path to post the artifacts in Artifactory
	destination = ARTIFACT_PATH + filename

	#next we define our REST API parameters, URL and auth
	url = BASE_ARTIFACT_URL + destination
	headers = {"X-Explode-Archive": "true"}
	auth = (USER, PASSWORD)

	#first make sure it's a clean directory
	CleanUp(localfilepath)
	
	try:

		#next we'll zip up the sources to a temporary location
		Zipfolder(ARTIFACT_SOURCES)
		
	except:
		print("DEBUG - Unable to zip up source files")		
	
	#ensuring we have the zip file - we'll attempt to upload the archive to Artifactory
	with open(localfilepath, 'rb') as zip_file:

		#we've got it open if we're here, so let's set the files parameter to the zip file
		files = {'file': (filename, zip_file, 'application/zip')}

		try:
			#now let's put the request in with our file and get the response
			resp = requests.put(url, auth=auth, headers=headers, data=zip_file)

			print("DEBUG - Server responded with: " + str(resp.status_code))

			#fail the Bamboo job with a non-zero exit code
			if (resp.status_code != 200):
				print ("DEBUG - Error uploading to Artifactory - not a blocker - proceeding")
		except:
			print ("DEBUG - Error uploading to Artifactory")						
	
	#if we're here - everything has gone well
	print ("DEBUG - Artifacts successfully uploaded to Artifactory")
	
	#regardless of status, we should clean up the zip file and remove it after use
	CleanUp(localfilepath)
			
if __name__ == "__main__": main()