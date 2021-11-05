'''
Copyright 2021 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Fri Nov 05 2021
File : report_artifacts_xlsx.py
'''
import logging

import re
import os
from datetime import datetime
import xlsxwriter

import _version

logger = logging.getLogger(__name__)

#------------------------------------------------------------------#
def generate_xlsx_report(reportData):
    logger.info("    Entering generate_xlsx_report")

    reportName = reportData["reportName"]
    projectName  = reportData["projectName"]
    projectNameForFile = re.sub(r"[^a-zA-Z0-9]+", '-', projectName )
    projectID = reportData["projectID"] 
    fileNameTimeStamp = reportData["fileNameTimeStamp"] 
    vulnerabilityDetails = reportData["vulnerabilityDetails"]
    projectList = reportData["projectList"]
    projectSummaryData = reportData["projectSummaryData"]
    applicationSummaryData = reportData["applicationSummaryData"]
    projectHierarchy = reportData["projectHierarchy"]
     

    cvssVersion = projectSummaryData["cvssVersion"]  # 2.0/3.x
    includeAssociatedFiles = projectSummaryData["includeAssociatedFiles"]  #True/False
    
    # Colors for report
    reveneraGray = '#323E48'
    white = '#FFFFFF'
    criticalVulnColor = "#400000"
    highVulnColor = "#C00000"
    mediumVulnColor = "#FFA500"
    lowVulnColor = "#FFFF00"
    noneVulnColor = "#D3D3D3"

    # Grab the current date/time for report date stamp
    now = datetime.now().strftime("%B %d, %Y at %H:%M:%S")

    if len(projectList)==1:
        xlsxFile = projectNameForFile + "-" + str(projectID) + "-" + reportName.replace(" ", "_") + "-" + fileNameTimeStamp + ".xlsx"
    else:
        xlsxFile = projectNameForFile + "-" + str(projectID)+ "-with-children-" + reportName.replace(" ", "_") + "-" + fileNameTimeStamp + ".xlsx" 

    logger.debug("xlsxFile: %s" %xlsxFile)

    # Create the workbook/worksheet for storying the data
    workbook = xlsxwriter.Workbook(xlsxFile)
    summaryWorksheet = workbook.add_worksheet('Vulnerability Summary') 
    summaryWorksheet.hide_gridlines(2)
    detailsWorksheet = workbook.add_worksheet('Vulnerability Details') 
    dataWorksheet = workbook.add_worksheet('Summary Data') 

    tableHeaderFormat = workbook.add_format()
    tableHeaderFormat.set_text_wrap()
    tableHeaderFormat.set_bold()
    tableHeaderFormat.set_bg_color(reveneraGray)
    tableHeaderFormat.set_font_color(white)
    tableHeaderFormat.set_font_size('12')
    tableHeaderFormat.set_align('center')
    tableHeaderFormat.set_align('vcenter')

    cellFormat = workbook.add_format()
    cellFormat.set_text_wrap()
    cellFormat.set_align('center')
    cellFormat.set_align('vcenter')
    cellFormat.set_font_size('10')
    cellFormat.set_border()
    
    cellDescriptionFormat = workbook.add_format()
    cellDescriptionFormat.set_text_wrap()
    cellDescriptionFormat.set_align('left')
    cellDescriptionFormat.set_align('vcenter')
    cellDescriptionFormat.set_font_size('10')
    cellDescriptionFormat.set_border()

    cellLinkFormat = workbook.add_format()
    cellLinkFormat.set_text_wrap()
    cellLinkFormat.set_align('center')
    cellLinkFormat.set_align('vcenter')
    cellLinkFormat.set_font_color('blue')
    cellLinkFormat.set_font_size('10')
    cellLinkFormat.set_underline()
    cellLinkFormat.set_border()

    boldCellFormat = workbook.add_format()
    boldCellFormat.set_align('vcenter')
    boldCellFormat.set_font_size('12')
    boldCellFormat.set_bold()

    # Create cell formats for the different vuln bands
    criticalVulnerabilityCell = workbook.add_format({'bg_color': criticalVulnColor,'font_color': white})
    highVulnerabilityCell = workbook.add_format({'bg_color': highVulnColor,'font_color':  white})
    mediumVulnerabilityCell = workbook.add_format({'bg_color': mediumVulnColor})
    lowVulnerabilityCell = workbook.add_format({'bg_color': lowVulnColor})

    #############################################################################
    #  Create the summary charts based on the data from the Summary Data tab
    #############################################################################

    defaultChartWidth = 700
    summaryChartHeight = 150
    catagoryHeaderRow = 6      # Where is the header row on the Summary Data sheet
    applicationSummaryRow = catagoryHeaderRow + 1  # Where is the summary data on the Summary Data sheet

    if len(projectList) > 1:
        summaryWorksheet.merge_range('B2:M2', "Project Hierarchy", tableHeaderFormat)
        summaryWorksheet.set_column('A:Z', 2)
                
        summaryWorksheet.write('C4', projectName, boldCellFormat) # Row 3, column 2
        display_project_hierarchy(summaryWorksheet, projectHierarchy, 3, 2, boldCellFormat)

        ############################################################################################################
        #  Vulnerability Summary Chart

        applicationVulnerabilitySummaryChart = workbook.add_chart({'type': 'bar', 'subtype': 'stacked'})
        applicationVulnerabilitySummaryChart.set_title({'name': 'Application Vulnerabilty Summary'})
        applicationVulnerabilitySummaryChart.set_size({'width': defaultChartWidth, 'height': summaryChartHeight})
        applicationVulnerabilitySummaryChart.set_legend({'position': 'bottom'})
        applicationVulnerabilitySummaryChart.set_y_axis({'reverse': True})

        if cvssVersion == "3.x": 
            vulnerabilityBarColors = [criticalVulnColor, highVulnColor, mediumVulnColor, lowVulnColor, noneVulnColor]
            vulnerabiltyDataStartColumn = 1 # Start data in Column B on the Summary Data sheet
        else:
            vulnerabilityBarColors = [highVulnColor, mediumVulnColor, lowVulnColor, noneVulnColor]
            vulnerabiltyDataStartColumn = 2 # Start data in Column C on the Summary Data sheet
        
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

    if cvssVersion == "3.x": 
        vulnerabilityBarColors = [criticalVulnColor, highVulnColor, mediumVulnColor, lowVulnColor, noneVulnColor]
        vulnerabiltyDataStartColumn = 1 # Start data in Column B
    else:
        vulnerabilityBarColors = [highVulnColor, mediumVulnColor, lowVulnColor, noneVulnColor]
        vulnerabiltyDataStartColumn = 2 # Start data in Column C
    
    for columnIndex in range(0, len(vulnerabilityBarColors)):

        projectVulnerabilitySummaryChart.add_series({ 
            'name':       ['Summary Data', catagoryHeaderRow, columnIndex+vulnerabiltyDataStartColumn], 
            'categories': ['Summary Data', applicationSummaryRow+1, columnIndex, applicationSummaryRow+1+len(projectList), columnIndex], 
            'values':     ['Summary Data', applicationSummaryRow+1, columnIndex+vulnerabiltyDataStartColumn, applicationSummaryRow+1+len(projectList), columnIndex+vulnerabiltyDataStartColumn],
            'fill':       {'color': vulnerabilityBarColors[columnIndex]}        }) 


    if len(projectList) == 1:
        summaryWorksheet.insert_chart('B2', projectVulnerabilitySummaryChart)
    else:
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
            
            components += componentName + " - " + componentVersionName + " (" + projectName + ")  \n"

        # Trim the last new line
        components=components[:-2]

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
        detailsWorksheet.write(row, 8, vulnerabilityDescription, cellDescriptionFormat)

        if includeAssociatedFiles:
            detailsWorksheet.write(row, 9, associatedFiles, cellDescriptionFormat)

        row+=1

    # Apply conditional formatting for the CVSS scores 
    if cvssVersion == "3.x": 
        detailsWorksheet.conditional_format(1,2, 1 + len(vulnerabilityDetails), 2, {'type': 'cell', 'criteria': 'between', 'minimum': 9, 'maximum': 10,'format': criticalVulnerabilityCell})
        detailsWorksheet.conditional_format(1,2, 1 + len(vulnerabilityDetails), 2, {'type': 'cell', 'criteria': 'between', 'minimum': 7, 'maximum': 8.9,'format': highVulnerabilityCell})
    else: 
        detailsWorksheet.conditional_format(1,2, 1 + len(vulnerabilityDetails), 2, {'type': 'cell', 'criteria': 'between', 'minimum': 7, 'maximum': 10,'format': highVulnerabilityCell})

    detailsWorksheet.conditional_format(1,2, 1 + len(vulnerabilityDetails), 2, {'type': 'cell', 'criteria': 'between', 'minimum': 4, 'maximum': 6.9,'format': mediumVulnerabilityCell})
    detailsWorksheet.conditional_format(1,2, 1 + len(vulnerabilityDetails), 2, {'type': 'cell', 'criteria': 'between', 'minimum': 0.1, 'maximum': 3.9,'format': lowVulnerabilityCell})

    # Automatically create the filter sort options
    detailsWorksheet.autofilter(0,0, 0 + len(vulnerabilityDetails)-1, len(tableHeaders)-1)


    #############################################################################
    #  Populate the Summary Data details
    #############################################################################

    dataWorksheet.merge_range('B1:F1', "Report Gernerated: %s" %(datetime.now().strftime("%B %d, %Y at %H:%M:%S")))
    dataWorksheet.merge_range('B2:F2', "Report Version: %s" %_version.__version__)

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

    return xlsxFile

#------------------------------------------------------------#
def display_project_hierarchy(worksheet, parentProject, row, column, boldCellFormat):

    column +=1 #  We are level down so we need to indent
    row +=1
    # Are there more child projects for this project?

    if len(parentProject["childProject"]):
        for childProject in parentProject["childProject"]:
            projectID = childProject["id"]
            projectName = childProject["name"]
            # Add this ID to the list of projects with other child projects
            # and get then do it again
            worksheet.write( row, column, projectName, boldCellFormat)

            row =  display_project_hierarchy(worksheet, childProject, row, column, boldCellFormat)
    return row
