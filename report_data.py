'''
Copyright 2020 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Fri Aug 07 2020
File : report_data.py
'''

import logging
import CodeInsight_RESTAPIs.project.get_project_inventory

logger = logging.getLogger(__name__)

#-------------------------------------------------------------------#
def gather_data_for_report(baseURL, projectID, authToken, reportName):
    logger.info("Entering gather_data_for_report")


    vulnerabilityDetails = {}

    # Grab the full project inventory
    full_project_inventory = CodeInsight_RESTAPIs.project.get_project_inventory.get_project_inventory_details(baseURL, projectID, authToken)
    projectName = full_project_inventory["projectName"]
    inventoryItems = full_project_inventory["inventoryItems"] 

    for inventoryItem in inventoryItems:
        inventoryID = inventoryItem["id"]
        componentName = inventoryItem["componentName"]
        componentVersionName = inventoryItem["componentVersionName"]

        try:
            vulnerabilities = inventoryItem["vulnerabilities"]

            # There is a key but see if there is any data
            if len(vulnerabilities):
                for vulnearbility in vulnerabilities:
                    vulnerabilityName = vulnearbility["vulnerabilityName"]

                    # Does it already exist and if so just append the component data
                    if vulnerabilityName in vulnerabilityDetails:
                        vulnerabilityDetails[vulnerabilityName]["affectedComponents"].append([inventoryID, componentName, componentVersionName ])
                    else:
                        # It's a new key so get all of the important data
                        vulnerabilityDetails[vulnerabilityName] = {}
                        vulnerabilityDetails[vulnerabilityName]["vulnerabilityDescription"] = vulnearbility["vulnerabilityDescription"]
                        vulnerabilityDetails[vulnerabilityName]["vulnerabilitySource"] = vulnearbility["vulnerabilitySource"]
                        vulnerabilityDetails[vulnerabilityName]["vulnerabilityUrl"] = vulnearbility["vulnerabilityUrl"]
                        vulnerabilityDetails[vulnerabilityName]["vulnerabilitySeverity"] = vulnearbility["vulnerabilityCvssV3Severity"]
                        vulnerabilityDetails[vulnerabilityName]["vulnerabilityScore"] = vulnearbility["vulnerabilityCvssV3Score"]
                        # Create a list of lists to hold the component data
                        vulnerabilityDetails[vulnerabilityName]["affectedComponents"] = []
                        vulnerabilityDetails[vulnerabilityName]["affectedComponents"].append([inventoryID, componentName, componentVersionName ])

            else:
                logger.debug("No vulnerabilities for % s - %s - %s" %(inventoryID, componentName, componentVersionName))
        except:
            logger.debug("No vulnerabilities for % s - %s - %s" %(inventoryID, componentName, componentVersionName))
  

    reportData = {}
    reportData["reportName"] = reportName
    reportData["projectName"] = projectName
    reportData["projectID"] = projectID
    reportData["baseURL"] = baseURL
    reportData["vulnerabilityDetails"] = vulnerabilityDetails

    return reportData


