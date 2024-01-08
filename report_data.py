'''
Copyright 2020 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Fri Aug 07 2020
File : report_data.py
'''

import logging
from collections import OrderedDict
import common.api.project.get_project_inventory
import common.api.project.get_child_projects
import common.api.project.get_project_information
import common.project_heirarchy

logger = logging.getLogger(__name__)

#-------------------------------------------------------------------#
def gather_data_for_report(baseURL, authToken, reportData):
    logger.info("Entering gather_data_for_report")

    projectID = reportData["projectID"]
    reportOptions = reportData["reportOptions"]

    # Parse report options
    includeChildProjects = reportOptions["includeChildProjects"]  # True/False
    cvssVersion = reportOptions["cvssVersion"]  # 2.0/3.x
    includeAssociatedFiles = reportOptions["includeAssociatedFiles"]  # True/False

    if cvssVersion == "3.x":
        cvssBaseVectorLink = "https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator?name="
    else:
        cvssBaseVectorLink = "https://nvd.nist.gov/vuln-metrics/cvss/v2-calculator?name="

    projectList = [] # List to hold parent/child details for report
    vulnerabilityDetails = {} # Create dictionary to hold all vulnerability data based on vul ID across all projects
    projectData = {} # Create a dictionary containing the project level summary data using projectID as keys

    projectList = common.project_heirarchy.create_project_heirarchy(baseURL, authToken, projectID, includeChildProjects)

    topLevelProjectName = projectList[0]["projectName"]
    # Get the list of parent/child projects start at the base project
    projectHierarchy = common.api.project.get_child_projects.get_child_projects_recursively(baseURL, projectID, authToken)


    # Collect details for each project
    for project in projectList:

        projectID = project["projectID"]
        projectName = project["projectName"]
        projectLink = project["projectLink"]  
        sortedVulnerabilityDetails = {}

        # Create empty dictionary for project level data for this project
        projectData[projectName] = {}

        if cvssVersion == "3.x":
            projectData[projectName]["numCriticalVulnerabilities"] = 0

        projectData[projectName]["numHighVulnerabilities"] = 0
        projectData[projectName]["numMediumVulnerabilities"] = 0
        projectData[projectName]["numLowVulnerabilities"] = 0
        projectData[projectName]["numNoneVulnerabilities"] = 0

        # Grab the full project inventory to get specific vulnerability details
        if includeAssociatedFiles:
            full_project_inventory = common.api.project.get_project_inventory.get_project_inventory_details(baseURL, projectID, authToken)
        else: 
            full_project_inventory = common.api.project.get_project_inventory.get_project_inventory_details_without_files(baseURL, projectID, authToken)
        
        inventoryItems = full_project_inventory["inventoryItems"] 

        for inventoryItem in inventoryItems:
            inventoryID = inventoryItem["id"]
            componentName = inventoryItem["componentName"]
            componentVersionName = inventoryItem["componentVersionName"]
            associatedFiles = inventoryItem["filePaths"]
            inventoryItemName = inventoryItem["name"]
            # This field was added in 2021R4 so if earlier release add the list
            try:
                customFields = inventoryItem["customFields"]
            except:
                customFields = [] 

            vulnerabilityIgnoreList = []
            # Create a list of the vulnerabilities to be ignored
            for customField in customFields:
                if customField["fieldLabel"] == "Vulnerability Ignore List":
                    ignoredCVEs = customField["value"]
                    if ignoredCVEs:
                        # Create a list from the string response and remove white space
                        for cve in ignoredCVEs.split('\n'):
                            cveValue = cve.split('|') # If a reason was provided for exclusion report
                            vulnerabilityIgnoreList.append(cveValue[0].strip())

            logger.debug("        Project:  %s   Inventory Name: %s  Inventory ID: %s" %(projectName, inventoryItemName, inventoryID))

            inventoryItemLink = baseURL + '''/codeinsight/FNCI#myprojectdetails/?id=''' + str(projectID) + '''&tab=projectInventory&pinv=''' + str(inventoryID)

            try:
                vulnerabilities = inventoryItem["vulnerabilities"]

                # There is a vulnerability key for this inventory item
                if len(vulnerabilities):
                    for vulnearbility in vulnerabilities:
                        vulnerabilityName = vulnearbility["vulnerabilityName"]
                        
                        if vulnerabilityName in vulnerabilityIgnoreList:
                            # Should this vulnerability be ignored?
                            logger.info("            Ignoring vulnerability %s for this component in project %s" %(vulnerabilityName, projectName))
                        
                        elif vulnerabilityName in vulnerabilityDetails and projectName in vulnerabilityDetails[vulnerabilityName]["affectedProjects"]:
                            # Is it already in the list for this project?
                            vulnerabilityDetails[vulnerabilityName]["affectedComponents"].append([inventoryID, componentName, componentVersionName, projectName, projectLink, inventoryItemLink, associatedFiles])
                        
                        else:
                            # This is a new vulnerability to track
                            vulnerabilityDetails[vulnerabilityName] = {}
                            vulnerabilityDetails[vulnerabilityName]["affectedProjects"] = [projectName]
                            vulnerabilityDetails[vulnerabilityName]["vulnerabilityDescription"] = vulnearbility["vulnerabilityDescription"]
                            vulnerabilityDetails[vulnerabilityName]["vulnerabilitySource"] = vulnearbility["vulnerabilitySource"]
                            vulnerabilityDetails[vulnerabilityName]["vulnerabilityUrl"] = vulnearbility["vulnerabilityUrl"]
                            
                            if cvssVersion == "3.x":
                                vulnerabilityDetails[vulnerabilityName]["vulnerabilitySeverity"] = vulnearbility["vulnerabilityCvssV3Severity"]
                                vulnerabilityDetails[vulnerabilityName]["vulnerabilityScore"] = vulnearbility["vulnerabilityCvssV3Score"]
                                vulnerabilityDetails[vulnerabilityName]["vulnerabilityVector"] = vulnearbility["vulnerabilityCvssV3Vector"]
                            else:
                                vulnerabilityDetails[vulnerabilityName]["vulnerabilitySeverity"] = vulnearbility["vulnerabilityCvssV2Severity"]
                                vulnerabilityDetails[vulnerabilityName]["vulnerabilityScore"] = vulnearbility["vulnerabilityCvssV2Score"]
                                vulnerabilityDetails[vulnerabilityName]["vulnerabilityVector"] = vulnearbility["vulnerabilityCvssV2Vector"]
                            
                            vulnerabilityDetails[vulnerabilityName]["publishedDate"] = vulnearbility["publishedDate"]
                            vulnerabilityDetails[vulnerabilityName]["modifiedDate"] = vulnearbility["modifiedDate"]

                            # Is there a vector link?
                            if vulnerabilityDetails[vulnerabilityName]["vulnerabilityVector"] != "N/A":
                                vulnerabilityDetails[vulnerabilityName]["vulnerabilityVectorLink"] = cvssBaseVectorLink + vulnerabilityName
                            else:
                                vulnerabilityDetails[vulnerabilityName]["vulnerabilityVectorLink"] = None

                            # Create a list of lists to hold the component data
                            vulnerabilityDetails[vulnerabilityName]["affectedComponents"] = []
                            vulnerabilityDetails[vulnerabilityName]["affectedComponents"].append([inventoryID, componentName, componentVersionName, projectName, projectLink, inventoryItemLink, associatedFiles])

                            # Increment count based on severity to account for ignore list
                            severity = vulnerabilityDetails[vulnerabilityName]["vulnerabilitySeverity"]
                            
                            if severity == "CRITICAL":
                                projectData[projectName]["numCriticalVulnerabilities"] +=1
                            elif severity== "HIGH":
                                projectData[projectName]["numHighVulnerabilities"] +=1
                            elif severity == "MEDIUM":
                                projectData[projectName]["numMediumVulnerabilities"] +=1
                            elif severity == "LOW":
                                projectData[projectName]["numLowVulnerabilities"] +=1
                            elif severity == "N/A":
                                projectData[projectName]["numNoneVulnerabilities"] +=1

                else:
                    # There is a vulnerability key in the reponse for this inventory item but it is empty
                    logger.debug("            No vulnerabilities for % s - %s   Inventory ID: %s" %(componentName, componentVersionName, inventoryID))

            except:
                # There was no vulnerability key in the reponse for this inventory item
                logger.debug("            No vulnerabilities for % s - %s   Inventory ID: %s" %(componentName, componentVersionName, inventoryID))


    # Sort the vulnerability dict by score (high to low)
    sortedVulnerabilityDetails = OrderedDict(sorted(vulnerabilityDetails.items(), key=lambda t: (  "-1" if t[1]["vulnerabilityScore"] == "N/A"  else str(t[1]["vulnerabilityScore"] )    )  ,               reverse=True ) )

    # Roll up the inventortory data at a project level for display charts
    projectSummaryData = create_project_summary_data_dict(projectData)
    projectSummaryData["cvssVersion"] = cvssVersion
    projectSummaryData["includeAssociatedFiles"] = includeAssociatedFiles

    # Roll up the individual project data to the application level
    applicationSummaryData = create_application_summary_data_dict(projectSummaryData)

    reportData["topLevelProjectName"] = topLevelProjectName
    reportData["projectName"] = projectHierarchy["name"]
    reportData["projectID"] = projectID
    reportData["vulnerabilityDetails"] = sortedVulnerabilityDetails
    reportData["projectList"] =projectList
    reportData["projectSummaryData"] = projectSummaryData
    reportData["applicationSummaryData"] = applicationSummaryData
    reportData["projectHierarchy"] = projectHierarchy

    return reportData

#----------------------------------------------------------------------------------------#
def create_project_summary_data_dict(projectData):
    logger.debug("Entering get_project_summary_data")

   # For the chart data we need to create lists where each element is in the correct order based on the 
   # project name order.  i.e. one list will # of approved items for each project in the correct order
    projectSummaryData = {}

    # Create empty lists for each metric that we need for the report
    for projectName in projectData:
        for metric in projectData[projectName]:
            if metric not in  ["P1InventoryItems", "projectLink"]:  # We don't care about these for now
                projectSummaryData[metric] = []

    # Grab the data for each project and add it in the correct order
    for projectName in projectData:
        for metric in projectData[projectName]:
            if metric not in  ["P1InventoryItems", "projectLink", "cvssVersion"]:  # We don't care about these for now
                projectSummaryData[metric].append(projectData[projectName][metric])

    projectSummaryData["projectNames"] = list(projectData.keys())
    
    logger.debug("Exiting get_project_summary_data")
    return projectSummaryData
    
#----------------------------------------------------------------------------------------#
def create_application_summary_data_dict(projectSummaryData):
    logger.debug("Entering get_application_summary_data")

    applicationSummaryData = {}

    # For each metric sum the data up
    for metric in projectSummaryData:
        if metric == "cvssVersion":
            applicationSummaryData[metric] = projectSummaryData[metric]
        elif metric != "projectNames" and metric != "includeAssociatedFiles":
            applicationSummaryData[metric] = sum(projectSummaryData[metric])

    logger.debug("Exiting get_application_summary_data")
    return applicationSummaryData