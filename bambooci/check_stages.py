import pyodbc 
import sys
import argparse

##########################################################################################################################################################
#
# Intel Corporation - Copyright 2017
#
# Description: Script used to check whether a given plan has all stages enabled. If not, it throws an exception and has a non-zero exit status (which)
# fails the calling job (e.g. Bamboo is the intended use) which conversely can do some error processing (in the case of Bamboo it would halt jobs)
#
# Params:
#	- Takes a single parameter, the build plan ID as recorded in Bamboo, e.g. ${bamboo.planKey} variable
#
# Assumptions/Requirements:
# 	- Bamboo agents must have pyodbc installed on them
#	- Bamboo system account has access to the production database (read-only)
#
##########################################################################################################################################################


#---------------------------------------------------------------------------------------------------------------------------------------------------------
# Define parameters for this script
#---------------------------------------------------------------------------------------------------------------------------------------------------------
parser = argparse.ArgumentParser(description='Check to ensure all stages are enabled')
parser.add_argument('-p', '--plan_key', required=True, help='Bamboo Plan Key to check to ensure all jobs are enabled')
args = vars(parser.parse_args())
PLAN_KEY = args['plan_key']

#---------------------------------------------------------------------------------------------------------------------------------------------------------
# Attempt a database connection info (assume trusted connection for Bamboo system account)
#---------------------------------------------------------------------------------------------------------------------------------------------------------
try:
	server = 'fm6vsql7101.amr.corp.intel.com,3180' 
	database = 'Bamboo' 
	cnxn = pyodbc.connect('Trusted_Connection=yes;DRIVER={SQL Server};SERVER='+server+';DATABASE='+database)
	cursor = cnxn.cursor()
except:
	print ("Unable to connect to database")
	sys.exit(-1)

#---------------------------------------------------------------------------------------------------------------------------------------------------------
# Attempt to execute the query to check to make sure stages are not disabled (SUSPENDED_FROM_BUILDING column)
#---------------------------------------------------------------------------------------------------------------------------------------------------------
try:
	cursor.execute('SELECT BUILD_ID ,BUILD_TYPE,FULL_KEY,BUILDKEY,TITLE,SUSPENDED_FROM_BUILDING FROM BUILD WHERE FULL_KEY LIKE \'' + PLAN_KEY + '%\'')
	rows = cursor.fetchall()
except:
	print("Unable to run query to check stage status for current plan")
	sys.exit(-1)

#---------------------------------------------------------------------------------------------------------------------------------------------------------
# Try to look at the values of all jobs to check if any are disabled
#---------------------------------------------------------------------------------------------------------------------------------------------------------
try:

	for row in rows:
		if (int(row.SUSPENDED_FROM_BUILDING) != 0):
			raise Exception ('Stage is disabled: ' + row.TITLE)

except Exception as error:
	print ("YOU SHALL NOT PASS! *staff smashes ground*")
	print ("Problem executing: " + repr(error))
	sys.exit(-1)

#---------------------------------------------------------------------------------------------------------------------------------------------------------
# Everything looks good! yay!
#---------------------------------------------------------------------------------------------------------------------------------------------------------
print ("SOLID! You haven't disabled anything - you may PASS!")
