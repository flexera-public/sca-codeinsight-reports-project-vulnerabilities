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
def gather_data_for_report(domainName, port, projectID, authToken, reportName):
    logger.info("Entering gather_data_for_report")


    # Create a dictionary containing the inveotry data using name/version strings as keys
    inventoryData = {}

    # Get details for  project
    try:
        projectInventoryResponse = CodeInsight_RESTAPIs.project.get_project_inventory.get_project_inventory_details(domainName, port, projectID, authToken)
    except:
        logger.error("    No project ineventory response!")
        print("No project inventory response.")
        return -1

    projectName = projectInventoryResponse["projectName"]
    inventoryItems = projectInventoryResponse["inventoryItems"]
    totalNumberIventory = len(inventoryItems)
    currentItem=0

    for inventoryItem in inventoryItems:
        currentItem +=1

        inventoryItemName = inventoryItem["name"]
        componentName = inventoryItem["componentName"]
        priority = inventoryItem["priority"]
        componentVersionName = inventoryItem["componentVersionName"]
        selectedLicenseName = inventoryItem["selectedLicenseName"]
        selectedLicenseSPDXIdentifier = inventoryItem["selectedLicenseSPDXIdentifier"]
        selectedLicensePriority = inventoryItem["selectedLicensePriority"]

        logger.debug("Processing iventory items %s of %s" %(currentItem, totalNumberIventory))
        logger.debug("    %s" %(inventoryItemName))
        
        try:
            vulnerabilities = inventoryItem["vulnerabilities"]
            vulnerabilityData = get_vulnerability_summary(vulnerabilities)
        except:
            logger.debug("No vulnerabilies for %s - %s" %(componentName, componentVersionName))
            vulnerabilityData = ""

        if selectedLicenseSPDXIdentifier != "":
            selectedLicenseName = selectedLicenseSPDXIdentifier

        inventoryData[inventoryItemName] = {
                                                "componentName" : componentName,
                                                "componentVersionName" : componentVersionName,
                                                "selectedLicenseName" : selectedLicenseName,
                                                "vulnerabilityData" : vulnerabilityData,
                                                "selectedLicensePriority" : selectedLicensePriority,
                                                "priority" : priority

                                            }
            

    reportData = {}
    reportData["reportName"] = reportName
    reportData["projectName"] = projectName
    reportData["inventoryData"] = inventoryData

    logger.info("Exiting gather_data_for_report")

    return reportData


#----------------------------------------------------------------------
def get_vulnerability_summary(vulnerabilities):
    logger.info("Entering get_vulnerability_summary")

    numCriticalVulnerabilities = 0
    numHighVulnerabilities = 0
    numMediumVulnerabilities = 0
    numLowVulnerabilities = 0
    numNoneVulnerabilities = 0
    vulnerabilityData = {}

    for vulnerability in vulnerabilities:

        vulnerabilityCvssV3Severity = vulnerability["vulnerabilityCvssV3Severity"]

        if vulnerabilityCvssV3Severity == "CRITICAL":
            numCriticalVulnerabilities +=1
        elif vulnerabilityCvssV3Severity == "HIGH":
            numHighVulnerabilities +=1
        elif vulnerabilityCvssV3Severity == "MEDIUM":
            numMediumVulnerabilities +=1
        elif vulnerabilityCvssV3Severity == "LOW":
            numLowVulnerabilities +=1
        elif vulnerabilityCvssV3Severity == "N/A":
            numNoneVulnerabilities +=1
        elif vulnerabilityCvssV3Severity == "NONE":
            numNoneVulnerabilities +=1            
        else:
            logger.error("Unknown vulnerability severity: %s" %vulnerabilityCvssV3Severity)

    vulnerabilityData["numCriticalVulnerabilities"] = numCriticalVulnerabilities
    vulnerabilityData["numHighVulnerabilities"] = numHighVulnerabilities
    vulnerabilityData["numMediumVulnerabilities"] = numMediumVulnerabilities
    vulnerabilityData["numLowVulnerabilities"] = numLowVulnerabilities
    vulnerabilityData["numNoneVulnerabilities"] = numNoneVulnerabilities

    return vulnerabilityData