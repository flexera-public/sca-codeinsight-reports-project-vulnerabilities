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


    vulnerabilityData = {}

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
            
                vulnerabilityData[inventoryID] = {}
                vulnerabilityData[inventoryID]["componentName"] = componentName
                vulnerabilityData[inventoryID]["componentVersionName"] = componentVersionName
                vulnerabilityData[inventoryID]["vulnerabilities"] = {}

                for vulnearbility in vulnerabilities:
                    vulnerabilityName = vulnearbility["vulnerabilityName"]

                    vulnerabilityData[inventoryID]["vulnerabilities"][vulnerabilityName] = []
                    vulnerabilityData[inventoryID]["vulnerabilities"][vulnerabilityName].append(vulnearbility["vulnerabilityDescription"])
                    vulnerabilityData[inventoryID]["vulnerabilities"][vulnerabilityName].append(vulnearbility["vulnerabilitySource"])
                    vulnerabilityData[inventoryID]["vulnerabilities"][vulnerabilityName].append(vulnearbility["vulnerabilityUrl"])
                    vulnerabilityData[inventoryID]["vulnerabilities"][vulnerabilityName].append(vulnearbility["vulnerabilityCvssV2Score"])
                    vulnerabilityData[inventoryID]["vulnerabilities"][vulnerabilityName].append(vulnearbility["vulnerabilityCvssV2Severity"])
                    vulnerabilityData[inventoryID]["vulnerabilities"][vulnerabilityName].append(vulnearbility["vulnerabilityCvssV3Score"])
                    vulnerabilityData[inventoryID]["vulnerabilities"][vulnerabilityName].append(vulnearbility["vulnerabilityCvssV3Severity"])
            else:
                logger.debug("No vulnerabilities for % s - %s - %s" %(inventoryID, componentName, componentVersionName))
        except:
            logger.debug("No vulnerabilities for % s - %s - %s" %(inventoryID, componentName, componentVersionName))
  

    reportData = {}
    reportData["reportName"] = reportName
    reportData["projectName"] = projectName
    reportData["projectID"] = projectID
    reportData["baseURL"] = baseURL
    reportData["vulnerabilityData"] = vulnerabilityData

    return reportData


