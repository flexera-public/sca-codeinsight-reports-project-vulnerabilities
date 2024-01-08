'''
Copyright 2021 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Fri Nov 05 2021
File : report_artifacts_xlsx.py
'''
import logging
import xlsxwriter

import common.branding.xlsx.xlsx_formatting
import _version

logger = logging.getLogger(__name__)

#------------------------------------------------------------------#
def generate_xlsx_report(reportData):
    logger.info("    Entering generate_xlsx_report")

    projectName  = reportData["projectName"]
    reportFileNameBase = reportData["reportFileNameBase"]
    reportTimeStamp =  reportData["reportTimeStamp"] 
    vulnerabilityDetails = reportData["vulnerabilityDetails"]
    projectList = reportData["projectList"]
    projectSummaryData = reportData["projectSummaryData"]
    applicationSummaryData = reportData["applicationSummaryData"]
    projectHierarchy = reportData["projectHierarchy"]
    
    cvssVersion = projectSummaryData["cvssVersion"]  # 2.0/3.x
    includeAssociatedFiles = projectSummaryData["includeAssociatedFiles"]  #True/False
    
    xlsxFile = reportFileNameBase + ".xlsx"

    # Create the workbook/worksheet for storying the data
    workbook = xlsxwriter.Workbook(xlsxFile)
    summaryWorksheet = workbook.add_worksheet('Vulnerability Summary') 
    summaryWorksheet.hide_gridlines(2)
    detailsWorksheet = workbook.add_worksheet('Vulnerability Details') 
    dataWorksheet = workbook.add_worksheet('Summary Data') 

    cellFormat = workbook.add_format(common.branding.xlsx.xlsx_formatting.standardCellFormatProperties)
    cellLinkFormat = workbook.add_format(common.branding.xlsx.xlsx_formatting.linkCellFormatProperties)
    hierarchyCellFormat = workbook.add_format(common.branding.xlsx.xlsx_formatting.hierarchyCellFormatProperties)
    tableHeaderFormat = workbook.add_format(common.branding.xlsx.xlsx_formatting.tableHeaderFormatProperties)

    # Create cell formats for the different vuln bands
    criticalVulnerabilityCellFormat = workbook.add_format(common.branding.xlsx.xlsx_formatting.criticalVulnerabilityCellFormat)
    highVulnerabilityCellFormat = workbook.add_format(common.branding.xlsx.xlsx_formatting.highVulnerabilityCellFormat)
    mediumVulnerabilityCellFormat = workbook.add_format(common.branding.xlsx.xlsx_formatting.mediumVulnerabilityCellFormat)
    lowVulnerabilityCellFormat = workbook.add_format(common.branding.xlsx.xlsx_formatting.lowVulnerabilityCellFormat)

    #############################################################################
    #  Create the summary charts based on the data from the Summary Data tab
    #############################################################################

    defaultChartWidth = 700
    summaryChartHeight = 150
    catagoryHeaderRow = 1      # Where is the header row on the Summary Data sheet
    applicationSummaryRow = catagoryHeaderRow + 1  # Where is the summary data on the Summary Data sheet


    if cvssVersion == "3.x": 
        vulnerabilityBarColors = [common.branding.xlsx.xlsx_formatting.criticalVulnColor, 
                                    common.branding.xlsx.xlsx_formatting.highVulnColor, 
                                    common.branding.xlsx.xlsx_formatting.mediumVulnColor, 
                                    common.branding.xlsx.xlsx_formatting.lowVulnColor, 
                                    common.branding.xlsx.xlsx_formatting.noneVulnColor]
        vulnerabiltyDataStartColumn = 1 # Start data in Column B on the Summary Data sheet
    else:
        vulnerabilityBarColors = [common.branding.xlsx.xlsx_formatting.highVulnColor, 
                                    common.branding.xlsx.xlsx_formatting.mediumVulnColor, 
                                    common.branding.xlsx.xlsx_formatting.lowVulnColor, 
                                    common.branding.xlsx.xlsx_formatting.noneVulnColor]
        vulnerabiltyDataStartColumn = 2 # Start data in Column C on the Summary Data sheet


    if len(projectList) > 1:

        summaryWorksheet.merge_range('B4:M4', "Project Hierarchy", tableHeaderFormat)
        summaryWorksheet.set_column('A:Z', 2)
                
        summaryWorksheet.write('C6', projectName, hierarchyCellFormat) # Row 5, column 2
        display_project_hierarchy(summaryWorksheet, projectHierarchy, 5, 2, hierarchyCellFormat)

        ############################################################################################################
        #  Vulnerability Summary Chart

        applicationVulnerabilitySummaryChart = workbook.add_chart({'type': 'bar', 'subtype': 'stacked'})
        applicationVulnerabilitySummaryChart.set_title({'name': 'Application Vulnerabilty Summary'})
        applicationVulnerabilitySummaryChart.set_size({'width': defaultChartWidth, 'height': summaryChartHeight})
        applicationVulnerabilitySummaryChart.set_legend({'position': 'bottom'})
        applicationVulnerabilitySummaryChart.set_y_axis({'reverse': True})
        
        for columnIndex in range(0, len(vulnerabilityBarColors)):

            applicationVulnerabilitySummaryChart.add_series({ 
                'name':       ['Summary Data', catagoryHeaderRow, columnIndex+vulnerabiltyDataStartColumn], 
                'categories': ['Summary Data', applicationSummaryRow, columnIndex, applicationSummaryRow, columnIndex], 
                'values':     ['Summary Data', applicationSummaryRow, columnIndex+vulnerabiltyDataStartColumn, applicationSummaryRow, columnIndex+vulnerabiltyDataStartColumn],
                'fill':       {'color': vulnerabilityBarColors[columnIndex]}            }) 
        
        summaryWorksheet.insert_chart('AA2', applicationVulnerabilitySummaryChart)
        

    ############################################################################################################
    #  Vulnerability Summary Chart
    projectVulnerabilitySummaryChart = workbook.add_chart({'type': 'bar', 'subtype': 'stacked'})

    if len(projectList) == 1:
        projectVulnerabilitySummaryChart.set_title({'name': 'Project Level Vulnerabilty Summary'})
    else:
        projectVulnerabilitySummaryChart.set_title({'name': 'Project Level Vulnerabilty Summaries'})

    projectVulnerabilitySummaryChart.set_size({'width': defaultChartWidth, 'height': summaryChartHeight + (len(projectList)* 30)})
    projectVulnerabilitySummaryChart.set_legend({'position': 'bottom'})
    projectVulnerabilitySummaryChart.set_y_axis({'reverse': True})
    
    for columnIndex in range(0, len(vulnerabilityBarColors)):

        projectVulnerabilitySummaryChart.add_series({ 
            'name':       ['Summary Data', catagoryHeaderRow, columnIndex+vulnerabiltyDataStartColumn], 
            'categories': ['Summary Data', applicationSummaryRow+1, columnIndex, applicationSummaryRow+1+len(projectList), columnIndex], 
            'values':     ['Summary Data', applicationSummaryRow+1, columnIndex+vulnerabiltyDataStartColumn, applicationSummaryRow+1+len(projectList), columnIndex+vulnerabiltyDataStartColumn],
            'fill':       {'color': vulnerabilityBarColors[columnIndex]}        }) 


    if len(projectList) == 1:
        summaryWorksheet.merge_range('A1:F1', "Report Generated: %s" %reportTimeStamp)
        summaryWorksheet.merge_range('A2:F2', "Report Version: %s" %_version.__version__)
        summaryWorksheet.insert_chart('B4', projectVulnerabilitySummaryChart)
    else:
        summaryWorksheet.merge_range('A1:U1', "Report Generated: %s" %reportTimeStamp)
        summaryWorksheet.merge_range('A2:U2', "Report Version: %s" %_version.__version__)
        summaryWorksheet.insert_chart('AA9', projectVulnerabilitySummaryChart)


    #############################################################################
    #  Populate the individual vulnerability details
    #############################################################################

    # Set the default column widths
    detailsWorksheet.set_column('A:A', 25)  # Vulnerability Name
    detailsWorksheet.set_column('B:B', 50)  # Component/project
    detailsWorksheet.set_column('C:C', 15)  # CVSS Score
    detailsWorksheet.set_column('D:D', 15)  # CVSS Severity
    detailsWorksheet.set_column('E:E', 30)  # CVSS Vector
    detailsWorksheet.set_column('F:F', 15)  # CVSS Source
    detailsWorksheet.set_column('G:G', 15)  # Published Date
    detailsWorksheet.set_column('H:H', 15)  # Last Modified Date
    detailsWorksheet.set_column('I:I', 60)  # Vulnerability Description
    if includeAssociatedFiles:
        detailsWorksheet.set_column('J:J', 60)  # Associated Files

    # Write the Column Headers
    row = 0
    column=0
    if cvssVersion == "3.x": 
        tableHeaders = ["VULNERABILITY", "COMPONENT", "CVSS v3.x SCORE", "SEVERITY", "CVSS v3.x VECTOR", "SOURCE","PUBLSIHED", "LAST MODIFIED", "DESCRIPTION"]
    else:
        tableHeaders = ["VULNERABILITY", "COMPONENT", "CVSS v2 SCORE", "SEVERITY", "CVSS v2 VECTOR", "SOURCE","PUBLSIHED", "LAST MODIFIED", "DESCRIPTION"]

    if includeAssociatedFiles:
        tableHeaders.append("ASSOCIATED FILES")

    detailsWorksheet.write_row(row, column , tableHeaders, tableHeaderFormat) # Write the col headers out
    row+=1

    # Cycle through each vulnerabiltty and add contects to sheet 
    for vulnerability in vulnerabilityDetails:

        vulnerabilityDescription = vulnerabilityDetails[vulnerability]["vulnerabilityDescription"]
        vulnerabilitySource = vulnerabilityDetails[vulnerability]["vulnerabilitySource"]
        vulnerabilityUrl = vulnerabilityDetails[vulnerability]["vulnerabilityUrl"]
        vulnerabilitySeverity = vulnerabilityDetails[vulnerability]["vulnerabilitySeverity"]
        vulnerabilityVector = vulnerabilityDetails[vulnerability]["vulnerabilityVector"]
        vulnerabilityVectorLink = vulnerabilityDetails[vulnerability]["vulnerabilityVectorLink"]
        vulnerabilityScore = vulnerabilityDetails[vulnerability]["vulnerabilityScore"]
        modifiedDate = vulnerabilityDetails[vulnerability]["modifiedDate"]
        publishedDate = vulnerabilityDetails[vulnerability]["publishedDate"]

        affectedComponents = vulnerabilityDetails[vulnerability]["affectedComponents"]

        components = ""
        # Sort by componentName and then version
        for affectedComponent in sorted(affectedComponents, key=lambda x: (x[1], x[2])):
            #inventoryID = affectedComponent[0]
            componentName = affectedComponent[1]
            componentVersionName = affectedComponent[2]
            projectName = affectedComponent[3]
            #projectLink = affectedComponent[4]
            inventoryItemLink = affectedComponent[5]
            
            if includeAssociatedFiles:
                associatedFiles = "\n".join(affectedComponent[6])
            
            if len(projectList) > 1:
                components += componentName + " - " + componentVersionName + " (" + projectName + ")  \n"
            else:
                components += componentName + " - " + componentVersionName + "\n"

        # Trim the last new line
        components = components.rstrip()

        # Now write each cell
        detailsWorksheet.write_url(row, 0, vulnerabilityUrl, cellLinkFormat, string=vulnerability)
        detailsWorksheet.write_url(row, 1, inventoryItemLink, cellLinkFormat, string=components)
        detailsWorksheet.write(row, 2, vulnerabilityScore, cellFormat)
        detailsWorksheet.write(row, 3, vulnerabilitySeverity, cellFormat)
        if vulnerabilityVectorLink:
            detailsWorksheet.write_url(row, 4, vulnerabilityVectorLink, cellLinkFormat, string=vulnerabilityVector)
        else:
            detailsWorksheet.write(row, 4, vulnerabilityVector, cellFormat)
        detailsWorksheet.write(row, 5, vulnerabilitySource, cellFormat)
        detailsWorksheet.write(row, 6, publishedDate, cellFormat)
        detailsWorksheet.write(row, 7, modifiedDate, cellFormat)
        detailsWorksheet.write(row, 8, vulnerabilityDescription, cellFormat)

        if includeAssociatedFiles:
            detailsWorksheet.write(row, 9, associatedFiles, cellFormat)

        row+=1

    # Apply conditional formatting for the CVSS scores 
    if cvssVersion == "3.x": 
        detailsWorksheet.conditional_format(1,2, 1 + len(vulnerabilityDetails), 2, {'type': 'cell', 'criteria': 'between', 'minimum': 9, 'maximum': 10,'format': criticalVulnerabilityCellFormat})
        detailsWorksheet.conditional_format(1,2, 1 + len(vulnerabilityDetails), 2, {'type': 'cell', 'criteria': 'between', 'minimum': 7, 'maximum': 8.9,'format': highVulnerabilityCellFormat})
    else: 
        detailsWorksheet.conditional_format(1,2, 1 + len(vulnerabilityDetails), 2, {'type': 'cell', 'criteria': 'between', 'minimum': 7, 'maximum': 10,'format': highVulnerabilityCellFormat})

    detailsWorksheet.conditional_format(1,2, 1 + len(vulnerabilityDetails), 2, {'type': 'cell', 'criteria': 'between', 'minimum': 4, 'maximum': 6.9,'format': mediumVulnerabilityCellFormat})
    detailsWorksheet.conditional_format(1,2, 1 + len(vulnerabilityDetails), 2, {'type': 'cell', 'criteria': 'between', 'minimum': 0.1, 'maximum': 3.9,'format': lowVulnerabilityCellFormat})

    # Automatically create the filter sort options
    if len(vulnerabilityDetails):
        detailsWorksheet.autofilter(0,0, 0 + len(vulnerabilityDetails)-1, len(tableHeaders)-1)


    #############################################################################
    #  Populate the Summary Data details
    #############################################################################

    # Add the summary data for bar graphs
    if cvssVersion == "3.x": 
        dataWorksheet.write('B' + str(catagoryHeaderRow +1) , "Critical")
    dataWorksheet.write('C' + str(catagoryHeaderRow +1) , "High")
    dataWorksheet.write('D' + str(catagoryHeaderRow +1) , "Medium")
    dataWorksheet.write('E' + str(catagoryHeaderRow +1) , "Low")
    dataWorksheet.write('F' + str(catagoryHeaderRow +1) , "None")

    dataWorksheet.write('A' + str(catagoryHeaderRow +2) , "Application Summary")
    dataWorksheet.write_column('A' + str(catagoryHeaderRow +3), projectSummaryData["projectNames"])

    if cvssVersion == "3.x": 
        dataWorksheet.write('B' + str(catagoryHeaderRow +2), applicationSummaryData["numCriticalVulnerabilities"])
        dataWorksheet.write_column('B' + str(catagoryHeaderRow +3), projectSummaryData["numCriticalVulnerabilities"])  

    dataWorksheet.write('C' + str(catagoryHeaderRow +2), applicationSummaryData["numHighVulnerabilities"])
    dataWorksheet.write_column('C' + str(catagoryHeaderRow +3), projectSummaryData["numHighVulnerabilities"])  

    dataWorksheet.write('D' + str(catagoryHeaderRow +2), applicationSummaryData["numMediumVulnerabilities"])
    dataWorksheet.write_column('D' + str(catagoryHeaderRow +3), projectSummaryData["numMediumVulnerabilities"])  

    dataWorksheet.write('E' + str(catagoryHeaderRow +2), applicationSummaryData["numLowVulnerabilities"])
    dataWorksheet.write_column('E' + str(catagoryHeaderRow +3), projectSummaryData["numLowVulnerabilities"])  

    dataWorksheet.write('F' + str(catagoryHeaderRow +2), applicationSummaryData["numNoneVulnerabilities"])
    dataWorksheet.write_column('F' + str(catagoryHeaderRow +3), projectSummaryData["numNoneVulnerabilities"])  

    workbook.close()

    logger.info("    Exiting generate_xlsx_report")

    return xlsxFile

#------------------------------------------------------------#
def display_project_hierarchy(worksheet, parentProject, row, column, boldCellFormat):

    column +=1 #  We are level down so we need to indent
    row +=1
    # Are there more child projects for this project?

    if len(parentProject["childProject"]):
        childProjects = parentProject["childProject"]
        childProjects.sort(key=lambda item: item.get("name"))

        for childProject in parentProject["childProject"]:
            projectName = childProject["name"]
            # Add this ID to the list of projects with other child projects
            # and get then do it again
            worksheet.write( row, column, projectName, boldCellFormat)

            row =  display_project_hierarchy(worksheet, childProject, row, column, boldCellFormat)
    return row
