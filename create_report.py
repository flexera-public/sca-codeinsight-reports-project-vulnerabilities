'''
Copyright 2020 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Fri Aug 07 2020
File : create_report.py
'''

import sys
import logging
import argparse
import zipfile
import os

import _version
import report_data
import report_artifacts
import CodeInsight_RESTAPIs.project.upload_reports

###################################################################################
# Test the version of python to make sure it's at least the version the script
# was tested on, otherwise there could be unexpected results
if sys.version_info <= (3, 5):
    raise Exception("The current version of Python is less than 3.5 which is unsupported.\n Script created/tested against python version 3.8.1. ")
else:
    pass

###################################################################################
#  Set up logging handler to allow for different levels of logging to be capture
logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', datefmt='%Y-%m-%d:%H:%M:%S', filename="_project_inventory_report.log", filemode='w',level=logging.DEBUG)
logger = logging.getLogger(__name__)

####################################################################################
# Create command line argument options
parser = argparse.ArgumentParser()
parser.add_argument('-pid', "--projectID", help="Project ID")
parser.add_argument("-rid", "--reportID", help="Report ID")
parser.add_argument("-authToken", "--authToken", help="Code Insight Authorization Token")
parser.add_argument("-domainName", "--domainName", help="Code Insight Core Server Domain Name")
parser.add_argument("-port", "--port", help="Code Insight Core Server Port")


#----------------------------------------------------------------------#
def main():

	reportName = "Project Inventory Report"

	logger.info("Creating %s - %s" %(reportName, _version.__version__))
	print("Creating %s - %s" %(reportName, _version.__version__))

	# See what if any arguments were provided
	args = parser.parse_args()
	projectID = args.projectID
	reportID = args.reportID
	authToken = args.authToken
	port = args.port
	domainName = args.domainName
	
	logger.debug("Custom Report Provided Arguments:")	
	logger.debug("    projectID:  %s" %projectID)	
	logger.debug("    reportID:   %s" %reportID)	
	logger.debug("    domainName:  %s" %domainName)	
	logger.debug("    port:  %s" %port)
	logger.debug("    authToken:  %s" %authToken)


	try:
		reportData = report_data.gather_data_for_report(domainName, port, projectID, authToken, reportName)
		print("    Report data has been collected")
	except:
		print("Error encountered while collecting report data.  Please see log for details")
		logger.error("Error encountered while collecting report data.")
		return -1

	try:
		reports = report_artifacts.create_report_artifacts(reportData)
		print("    Report artifacts have been created")
	except:
		print("Error encountered while creating report artifacts.  Please see log for details")
		logger.error("Error encountered while creating report artifacts.")
		return -1

	#########################################################
	# Create zip file to be uploaded to Code Insight
	try:
		uploadZipfile = create_report_zipfile(reports, reportName)
		print("    Upload zip file creation completed")
	except:
		print("Error created zip archive for upload. Please see log for details")
		logger.error("Error created zip archive for upload.")
		return -1

	#########################################################
	# Upload the file to Code Insight
	try:
		CodeInsight_RESTAPIs.project.upload_reports.upload_project_report_data(domainName, port, projectID, reportID, authToken, uploadZipfile)
	except:
		print("Error uploading archive to Code Insight")
		logger.error("Error uploading archive to Code Insight.")
		return -1

	#########################################################
	# Remove the file since it has been uploaded to Code Insight
	try:
		os.remove(uploadZipfile)
	except OSError:
		logger.error("Error removing %s" %uploadZipfile)
		print("Error removing %s" %uploadZipfile)

	logger.info("Completed creating %s" %reportName)
	print("Completed creating %s" %reportName)

#---------------------------------------------------------------------#
def create_report_zipfile(reportOutputs, reportName):
	logger.info("Entering create_report_zipfile")

	# create a ZipFile object
	allFormatZipFile = reportName + ".zip"
	allFormatsZip = zipfile.ZipFile(allFormatZipFile, 'w', zipfile.ZIP_DEFLATED)

	logger.debug("     	  Create downloadable archive: %s" %allFormatZipFile)
	print("        Create downloadable archive: %s" %allFormatZipFile)
	for format in reportOutputs["allFormats"]:
		print("            Adding %s to zip" %format)
		logger.debug("    Adding %s to zip" %format)
		allFormatsZip.write(format)

	allFormatsZip.close()
	logger.debug(    "Downloadable archive created")
	print("        Downloadable archive created")

	# Now create a temp zipfile of the zipfile along with the viewable file itself
	uploadZipflle = reportName + "_upload.zip"
	print("        Create zip archive containing viewable and downloadable archive for upload: %s" %uploadZipflle)
	logger.debug("    Create zip archive containing viewable and downloadable archive for upload: %s" %uploadZipflle)
	zipToUpload = zipfile.ZipFile(uploadZipflle, 'w', zipfile.ZIP_DEFLATED)
	zipToUpload.write(reportOutputs["viewable"])
	zipToUpload.write(allFormatZipFile)
	zipToUpload.close()
	logger.debug("    Archive zip file for upload has been created")
	print("        Archive zip file for upload has been created")

	# Clean up the items that were added to the zipfile
	try:
		os.remove(allFormatZipFile)
	except OSError:
		logger.error("Error removing %s" %allFormatZipFile)
		print("Error removing %s" %allFormatZipFile)
		return -1

	for fileName in reportOutputs["allFormats"]:
		try:
			os.remove(fileName)
		except OSError:
			logger.error("Error removing %s" %fileName)
			print("Error removing %s" %fileName)
			return -1    

	logger.info("Exiting create_report_zipfile")
	return uploadZipflle



#----------------------------------------------------------------------#    
if __name__ == "__main__":
    main()  