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
import CodeInsight_RESTAPIs.project.get_project_inventory
import CodeInsight_RESTAPIs.project.get_child_projects
import CodeInsight_RESTAPIs.project.get_project_information



logger = logging.getLogger(__name__)

#-------------------------------------------------------------------#
def gather_data_for_report(baseURL, projectID, authToken, reportName, reportOptions):
    logger.info("Entering gather_data_for_report")

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


    # Get the list of parent/child projects start at the base project
    projectHierarchy = CodeInsight_RESTAPIs.project.get_child_projects.get_child_projects_recursively(baseURL, projectID, authToken)

    # Create a list of project data sorted by the project name at each level for report display  
    # Add details for the parent node
    nodeDetails = {}
    nodeDetails["parent"] = "#"  # The root node
    nodeDetails["projectName"] = projectHierarchy["name"]
    nodeDetails["projectID"] = projectHierarchy["id"]
    nodeDetails["projectLink"] = baseURL + "/codeinsight/FNCI#myprojectdetails/?id=" + str(projectHierarchy["id"]) + "&tab=projectInventory"

    projectList.append(nodeDetails)

    if includeChildProjects:
        projectList = create_project_hierarchy(projectHierarchy, projectHierarchy["id"], projectList, baseURL)
    else:
        logger.debug("Child hierarchy disabled")

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
        full_project_inventory = CodeInsight_RESTAPIs.project.get_project_inventory.get_project_inventory_details(baseURL, projectID, authToken)
        
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
                        vulnerabilityIgnoreList = [cve.strip() for cve in ignoredCVEs.split('\n')]

            logger.debug("        Project:  %s   Inventory Name: %s  Inventory ID: %s" %(projectName, inventoryItemName, inventoryID))

            inventoryItemLink = baseURL + '''/codeinsight/FNCI#myprojectdetails/?id=''' + str(projectID) + '''&tab=projectInventory&pinv=''' + str(inventoryID)

            try:
                vulnerabilities = inventoryItem["vulnerabilities"]

                # There is a key but see if there is any data
                if len(vulnerabilities):
                    for vulnearbility in vulnerabilities:
                        vulnerabilityName = vulnearbility["vulnerabilityName"]
                        
                        if vulnerabilityName in vulnerabilityIgnoreList:
                            # Should this vulnerability be ignored?
                            logger.info("            Ignoring vulnerability %s for this component" %(vulnerabilityName))
                        elif vulnerabilityName in vulnerabilityDetails:
                            # Does it already exist and if so just append the component data
                            vulnerabilityDetails[vulnerabilityName]["affectedComponents"].append([inventoryID, componentName, componentVersionName, projectName, projectLink, inventoryItemLink, associatedFiles])
                        else:
                            # It's a new key so get all of the important data
                            vulnerabilityDetails[vulnerabilityName] = {}
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
                            if (vulnerabilityDetails[vulnerabilityName]["vulnerabilitySeverity"]) == "CRITICAL":
                                projectData[projectName]["numCriticalVulnerabilities"] +=1
                            elif (vulnerabilityDetails[vulnerabilityName]["vulnerabilitySeverity"]) == "HIGH":
                                projectData[projectName]["numHighVulnerabilities"] +=1
                            elif (vulnerabilityDetails[vulnerabilityName]["vulnerabilitySeverity"]) == "MEDIUM":
                                projectData[projectName]["numMediumVulnerabilities"] +=1
                            elif (vulnerabilityDetails[vulnerabilityName]["vulnerabilitySeverity"]) == "LOW":
                                projectData[projectName]["numLowVulnerabilities"] +=1
                            elif (vulnerabilityDetails[vulnerabilityName]["vulnerabilitySeverity"]) == "N/A":
                                projectData[projectName]["numNoneVulnerabilities"] +=1

                else:
                    logger.debug("            No vulnerabilities for % s - %s   Inventory ID: %s" %(componentName, componentVersionName, inventoryID))

            except:
                logger.debug("            No vulnerabilities for % s - %s   Inventory ID: %s" %(componentName, componentVersionName, inventoryID))


    # Sort the vulnerability dict by score (high to low)
    sortedVulnerabilityDetails = OrderedDict(sorted(vulnerabilityDetails.items(), key=lambda t: (  "-1" if t[1]["vulnerabilityScore"] == "N/A"  else str(t[1]["vulnerabilityScore"] )    )  ,               reverse=True ) )

    # Roll up the inventortory data at a project level for display charts
    projectSummaryData = create_project_summary_data_dict(projectData)
    projectSummaryData["cvssVersion"] = cvssVersion
    projectSummaryData["includeAssociatedFiles"] = includeAssociatedFiles

    # Roll up the individual project data to the application level
    applicationSummaryData = create_application_summary_data_dict(projectSummaryData)

    reportData = {}
    reportData["reportName"] = reportName
    reportData["projectName"] = projectHierarchy["name"]
    reportData["projectID"] = projectID
    reportData["vulnerabilityDetails"] = sortedVulnerabilityDetails
    reportData["projectList"] =projectList
    reportData["projectSummaryData"] = projectSummaryData
    reportData["applicationSummaryData"] = applicationSummaryData
    reportData["projectHierarchy"] = projectHierarchy

    return reportData

#----------------------------------------------#
def create_project_hierarchy(project, parentID, projectList, baseURL):
    logger.debug("Entering create_project_hierarchy with parentID : %s" %parentID)

    # Are there more child projects for this project?
    if len(project["childProject"]):

        # Sort by project name of child projects
        for childProject in sorted(project["childProject"], key = lambda i: i['name'] ) :

            nodeDetails = {}
            nodeDetails["projectID"] = childProject["id"]
            nodeDetails["parent"] = parentID
            nodeDetails["projectName"] = childProject["name"]
            nodeDetails["projectLink"] = baseURL + "/codeinsight/FNCI#myprojectdetails/?id=" + str(childProject["id"]) + "&tab=projectInventory"

            projectList.append( nodeDetails )

            create_project_hierarchy(childProject, childProject["id"], projectList, baseURL)

    return projectList


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