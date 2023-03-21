'''
Copyright 2023 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Fri Feb 24 2023
File : registration.py
'''
import sys, os, logging, argparse, json, stat

import CodeInsight_RESTAPIs.reports.get_reports
import CodeInsight_RESTAPIs.reports.create_report
import CodeInsight_RESTAPIs.reports.delete_report
import CodeInsight_RESTAPIs.reports.update_report

###################################################################################
# Test the version of python to make sure it's at least the version the script
# was tested on, otherwise there could be unexpected results
if sys.version_info <= (3, 6):
    raise Exception("The current version of Python is less than 3.6 which is unsupported.\n Script created/tested against python version 3.10.1. ")
else:
    pass

logfilePath = os.path.dirname(os.path.realpath(__file__)) 
logfileName = "_" + os.path.basename(__file__).split('.')[0] + ".log"
logfile = os.path.join(logfilePath, logfileName)

propertiesFile = "../server_properties.json"  # Created by installer or manually
configurationFile = "registration_config.json"

###################################################################################
#  Set up logging handler to allow for different levels of logging to be capture
logging.basicConfig(format='%(asctime)s,%(msecs)-3d  %(levelname)-8s [%(filename)-30s:%(lineno)-4d]  %(message)s', datefmt='%Y-%m-%d:%H:%M:%S', filename=logfile, filemode='w',level=logging.DEBUG)
logger = logging.getLogger(__name__)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)  # Disable logging for module

#####################################################################################################
#  Code Insight System Information
#  See if there is a common file for config details
if os.path.exists(propertiesFile):
    try:
        file_ptr = open(propertiesFile, "r")
        configData = json.load(file_ptr)
        file_ptr.close()
        logger.info("Loading config data from properties file: %s" %propertiesFile)

        # The file exists so can we get the config data from it?
        if "core.server.url" in configData:
            baseURL = configData["core.server.url"]
        else:
            baseURL = "http://localhost:8888"
        
        if "core.server.token" in configData:
            adminAuthToken = configData["core.server.token"]
        else:
            adminAuthToken = "UPDATEME" 
    except:
        logger.error("Unable to open properties file: %s" %propertiesFile)

else:
    logger.info("Using config data from registration.py")
    baseURL = "UPDATEME" # i.e. http://localhost:8888 or https://sca.mycodeinsight.com:8443 
    adminAuthToken = "UPDATEME"

#####################################################################################################
# Quick sanity check
if adminAuthToken == "UPDATEME" or baseURL == "UPDATEME":
    message = "Ensure baseURL and the admin authorization token have been updated within registration.py or server_properties.json"
    logger.error(message)
    print(message)
    sys.exit()

#####################################################################################################
# Manage report option data
if os.path.exists(configurationFile):
    try:
        file_ptr = open(configurationFile, "r")
        configData = json.load(file_ptr)
        file_ptr.close()
        logger.info("Loading config data from properties file: %s" %configurationFile)
    except:
        logger.error("Unable to open properties file: %s" %configurationFile)
        print("Unable to open properties file: %s" %configurationFile)
        sys.exit()
else:
    logger.error("Report configuration file %s does not exist" %configurationFile)
    print("Report configuration file %s does not exist" %configurationFile)
    sys.exit()

reportName = configData["reportName"]
enableProjectPickerValue = configData["enableProjectPickerValue"]
reportOptions = configData["reportOptions"]

#####################################################################################################
# Get the directory name in order to register the script
# this will be based on the git repo name is some cases
currentFolderName = os.path.basename(os.getcwd())

#####################################################################################################
# The path with the custom_report_scripts folder to called via the framework
if sys.platform.startswith('linux'):
    reportHelperScript = "create_report.sh"
elif sys.platform == "win32":
    reportHelperScript = "create_report.bat"
else:
    sys.exit("No script file for operating system")

reportPath = currentFolderName + "/" + reportHelperScript     

# Create command line argument options
parser = argparse.ArgumentParser()
parser.add_argument('-reg', "--register", action='store_true', help="Register custom reports")
parser.add_argument("-unreg", "--unregister", action='store_true', help="Unegister custom reports")
parser.add_argument("-update", "--update", action='store_true', help="Update a registered custom reports")

#----------------------------------------------------------------------#
def main():
    # See what if any arguments were provided
    args = parser.parse_args()

    if args.register and args.unregister:
        # You can use both options at the same time
        parser.print_help(sys.stderr)
    elif args.register:
        register_custom_reports()
        if sys.platform.startswith('linux'):
            # Make the shell script executable
            os.chmod(reportHelperScript, os.stat(reportHelperScript).st_mode | stat.S_IEXEC)
    elif args.unregister:
        unregister_custom_reports()
    elif args.update:
        update_custom_reports()
    else:
        parser.print_help(sys.stderr)

#-----------------------------------------------------------------------#
def register_custom_reports():
    logger.debug("Entering register_custom_reports")

    # Get the current reports so we can ensure the indexes of the new reports have no conflicts
    response = CodeInsight_RESTAPIs.reports.get_reports.get_all_currently_registered_reports(baseURL, adminAuthToken)
    
    if "error" in response:
        if "Status 401 – Unauthorized" in response["error"]:
            print("Supplied token does not have admin privileges.")
            logger.error("Supplied token does not have admin privileges.")
        else:
            logger.error("Error getting register reports:  %s" %response)
            print("Error getting register reports:  %s" %response)
        sys.exit()

    # Determine the maximun ID of any current report
    maxReportOrder = max(response, key=lambda x:x['id'])["order"]
    reportOrder = maxReportOrder + 1

    logger.info("Attempting to register %s with a report order of %s" %(reportName, reportOrder))
    print("Attempting to register %s with a report order of %s" %(reportName, reportOrder))

    response = CodeInsight_RESTAPIs.reports.create_report.register_report(reportName, reportPath, reportOrder, enableProjectPickerValue, reportOptions, baseURL, adminAuthToken)

    if "error" in response:
        if "Unrecognized field" in response["error"]:
            print("Unrecognized field within update body. See log for details")
            logger.error("Unrecognized field within update body. See log for details") 
        elif "Status 401 - Unauthorized" in response["error"]:
            print("Supplied token does not have admin privileges.")
            logger.error("Supplied token does not have admin privileges.")
        elif "already exists. Enter a different name" in response["error"]:
            print("A report by this name has aleady been registered. Did you mean to update?")
            logger.error("A report by this name has aleady been registered. Did you mean to update?")
        else:
            logger.error(response)
            print("Error getting report details:  %s" %response)
        sys.exit()

    reportID = response["id"]
    print("Report registration succeeded! %s has been registered with a report ID of %s" %(reportName, reportID))
    logger.info("Report registration succeeded! %s has been registered with a report ID of %s" %(reportName, reportID))

#-----------------------------------------------------------------------#
def unregister_custom_reports():
    logger.debug("Entering unregister_custom_reports")

    # 2023R1 removed the ability to unregister a report by name so attempt to unregister by ID first
    # and then default back to name to support older releases
    response = CodeInsight_RESTAPIs.reports.get_reports.get_all_currently_registered_reports_by_name(baseURL, adminAuthToken, reportName)

    if "error" in response:
        if "Total records :0 number of pages :0" in response["error"]:
            print("%s is not currently registered." %reportName)
            logger.error("%s is not currently registered." %reportName)
        else:
            logger.error(response)
            print("Error getting report details:  %s" %response)
        sys.exit()
    
    reportId = response[0]["id"]

    response = CodeInsight_RESTAPIs.reports.delete_report.unregister_report_by_id(baseURL, adminAuthToken, reportId)

    if "error" in response:
        # There was an error so try via the report name
        response = CodeInsight_RESTAPIs.reports.delete_report.unregister_report_by_name(baseURL, adminAuthToken, reportName)
        print("%s has been unregistered." %reportName)
        logger.info("%s has been unregistered."%reportName)

    else:
        print("%s has been unregistered." %reportName)
        logger.info("%s has been unregistered."%reportName)
        

#-----------------------------------------------------------------------#
def update_custom_reports():
    logger.debug("Entering update_custom_reports")

    response = CodeInsight_RESTAPIs.reports.get_reports.get_all_currently_registered_reports_by_name(baseURL, adminAuthToken, reportName)

    if "error" in response:
        if "Total records :0 number of pages :0" in response["error"]:
            print("%s is not currently registered." %reportName)
            logger.error("%s is not currently registered." %reportName)
        elif "Status 401 - Unauthorized" in response["error"]:
            print("Supplied token does not have admin privileges.")
            logger.error("Supplied token does not have admin privileges.")
        else:
            logger.error(response)
            print("Error getting report details:  %s" %response)
        sys.exit() 

    reportID = response[0]["id"]
    reportOrder = response[0]["order"]

    logger.info("Attempting to update %s with a report id of %s" %(reportName, reportID))
    print("Attempting to update %s with a report id of %s" %(reportName, reportID))

    response = CodeInsight_RESTAPIs.reports.update_report.update_custom_report(reportName, reportPath, reportID, reportOrder, enableProjectPickerValue, reportOptions, baseURL, adminAuthToken)

    if "error" in response:
        if "Unrecognized field" in response["error"]:
            print("Unrecognized field within update body. See log for details")
            logger.error("Unrecognized field within update body. See log for details")
        elif "Status 401 - Unauthorized" in response["error"]:
            print("Supplied token does not have admin privileges.")
            logger.error("Supplied token does not have admin privileges.")
        else:
            logger.error(response)
            print("Error getting report details:  %s" %response)
        sys.exit()
    elif "message" in response:
        print("%s" %response["message"])
        logger.info("%s" %response["message"])
    else:
        logger.error("Unrecognized response")



#----------------------------------------------------------------------#    
if __name__ == "__main__":
    main()    
