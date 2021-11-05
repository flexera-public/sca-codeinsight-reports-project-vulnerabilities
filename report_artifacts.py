'''
Copyright 2020 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Fri Aug 07 2020
File : report_artifacts.py
'''

import logging
import os
from datetime import datetime
import base64
import xlsxwriter
import re

import _version

logger = logging.getLogger(__name__)

#--------------------------------------------------------------------------------#
def create_report_artifacts(reportData):
    logger.info("Entering create_report_artifacts")

    # Dict to hold the complete list of reports
    reports = {}

    htmlFile = generate_html_report(reportData)
    xlsxFile = generate_xlsx_report(reportData)
    
    reports["viewable"] = htmlFile
    reports["allFormats"] = [htmlFile, xlsxFile]

    logger.info("Exiting create_report_artifacts")
    
    return reports 


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


#------------------------------------------------------------------#
def generate_html_report(reportData):
    logger.info("    Entering generate_html_report")


    reportName = reportData["reportName"]
    projectName  = reportData["projectName"]
    projectNameForFile = re.sub(r"[^a-zA-Z0-9]+", '-', projectName )
    projectID = reportData["projectID"] 
    fileNameTimeStamp = reportData["fileNameTimeStamp"] 
    vulnerabilityDetails = reportData["vulnerabilityDetails"]
    projectList = reportData["projectList"]
    projectSummaryData = reportData["projectSummaryData"]
    applicationSummaryData = reportData["applicationSummaryData"]

    cvssVersion = projectSummaryData["cvssVersion"]  # 2.0/3.x
    includeAssociatedFiles = projectSummaryData["includeAssociatedFiles"]  #True/False
    
    scriptDirectory = os.path.dirname(os.path.realpath(__file__))
    cssFile =  os.path.join(scriptDirectory, "report_branding/css/revenera_common.css")
    logoImageFile =  os.path.join(scriptDirectory, "report_branding/images/logo_reversed.svg")
    iconFile =  os.path.join(scriptDirectory, "report_branding/images/favicon-revenera.ico")
    statusApprovedIcon = os.path.join(scriptDirectory, "report_brandings/images/status_approved_selected.png")
    statusRejectedIcon = os.path.join(scriptDirectory, "report_branding/images/status_rejected_selected.png")
    statusDraftIcon = os.path.join(scriptDirectory, "report_branding/images/status_draft_ready_selected.png")

    logger.debug("cssFile: %s" %cssFile)
    logger.debug("imageFile: %s" %logoImageFile)
    logger.debug("iconFile: %s" %iconFile)
    logger.debug("statusApprovedIcon: %s" %statusApprovedIcon)
    logger.debug("statusRejectedIcon: %s" %statusRejectedIcon)
    logger.debug("statusDraftIcon: %s" %statusDraftIcon)


    #########################################################
    #  Encode the image files
    encodedLogoImage = encodeImage(logoImageFile)
    encodedfaviconImage = encodeImage(iconFile)

    # Grab the current date/time for report date stamp
    now = datetime.now().strftime("%B %d, %Y at %H:%M:%S")
    
    if len(projectList)==1:
        htmlFile = projectNameForFile + "-" + str(projectID) + "-" + reportName.replace(" ", "_") + "-" + fileNameTimeStamp + ".html"
    else:
        htmlFile = projectNameForFile + "-" + str(projectID)+ "-with-children-" + reportName.replace(" ", "_") + "-" + fileNameTimeStamp + ".html" 
        
    logger.debug("htmlFile: %s" %htmlFile)

    #---------------------------------------------------------------------------------------------------
    # Create a simple HTML file to display
    #---------------------------------------------------------------------------------------------------
    try:
        html_ptr = open(htmlFile,"w")
    except:
        logger.error("Failed to open htmlfile %s:" %htmlFile)
        raise

    html_ptr.write("<html>\n") 
    html_ptr.write("    <head>\n")

    html_ptr.write("        <!-- Required meta tags --> \n")
    html_ptr.write("        <meta charset='utf-8'>  \n")
    html_ptr.write("        <meta name='viewport' content='width=device-width, initial-scale=1, shrink-to-fit=no'> \n")

    html_ptr.write(''' 
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.1/css/bootstrap.min.css" integrity="sha384-VCmXjywReHh4PwowAiWNagnWcLhlEJLA5buUprzK8rxFgeH0kww/aWY76TfkUoSX" crossorigin="anonymous">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/4.1.3/css/bootstrap.css">
        <link rel="stylesheet" href="https://cdn.datatables.net/1.10.21/css/dataTables.bootstrap4.min.css">
    ''')


    html_ptr.write("        <style>\n")

    # Add the contents of the css file to the head block
    try:
        f_ptr = open(cssFile)
        logger.debug("Adding css file details")
        for line in f_ptr:
            html_ptr.write("            %s" %line)
        f_ptr.close()
    except:
        logger.error("Unable to open %s" %cssFile)
        print("Unable to open %s" %cssFile)

    html_ptr.write("        </style>\n")  

    html_ptr.write("    	<link rel='icon' type='image/png' href='data:image/png;base64, {}'>\n".format(encodedfaviconImage.decode('utf-8')))
    html_ptr.write("        <title>%s</title>\n" %(reportName.upper()))
    html_ptr.write("    </head>\n") 

    html_ptr.write("<body>\n")
    html_ptr.write("<div class=\"container-fluid\">\n")

    #---------------------------------------------------------------------------------------------------
    # Report Header
    #---------------------------------------------------------------------------------------------------
    html_ptr.write("<!-- BEGIN HEADER -->\n")
    html_ptr.write("<div class='header'>\n")
    html_ptr.write("  <div class='logo'>\n")
    html_ptr.write("    <img src='data:image/svg+xml;base64,{}' style='width: 400px;'>\n".format(encodedLogoImage.decode('utf-8')))
    html_ptr.write("  </div>\n")
    html_ptr.write("<div class='report-title'>%s</div>\n" %reportName)
    html_ptr.write("</div>\n")
    html_ptr.write("<!-- END HEADER -->\n")

    #---------------------------------------------------------------------------------------------------
    # Body of Report
    #---------------------------------------------------------------------------------------------------
    html_ptr.write("<!-- BEGIN BODY -->\n")  

    #######################################################################
    #  Create table to hold the application summary charts.
    #  js script itself is added later
    html_ptr.write("<table id='applicationSummary' class='table' style='width:90%'>\n")
    html_ptr.write("    <thead>\n")
    html_ptr.write("        <tr>\n")
    if len(projectList) > 1:
        html_ptr.write("            <th colspan='8' class='text-center'><h4>Application Summary</h4></th>\n") 
    else:
        html_ptr.write("            <th colspan='8' class='text-center'><h4>%s Summary</h4></th>\n" %projectName) 
    html_ptr.write("        </tr>\n") 
    html_ptr.write("    </thead>\n")
    html_ptr.write("</table>\n")
    
    html_ptr.write("<div class='container'>\n")
    html_ptr.write("    <div class='row'>\n")
    html_ptr.write("        <div class='col-sm'>\n")
    html_ptr.write("            <canvas id='applicationVulnerabilities'></canvas>\n")
    html_ptr.write("         </div>\n")
    html_ptr.write("    </div>\n")
    html_ptr.write("</div>\n")


    # If there is some sort of hierarchy then show specific project summeries
    if len(projectList) > 1:
        
        # How much space to we need to give each canvas
        # based on the amount of projects in the hierarchy
        canvasHeight = len(projectList) * 30   

        # We need a minimum size to cover font as well
        if canvasHeight < 180:
            canvasHeight = 180
        # The entire column needs to the vulnerability summary
        columnHeight = canvasHeight

        html_ptr.write("<hr class='small'>\n")

        #######################################################################
        #  Create table to hold the project summary charts.
        #  js script itself is added later

        html_ptr.write("<table id='projectSummary' class='table' style='width:90%'>\n")
        html_ptr.write("    <thead>\n")
        html_ptr.write("        <tr>\n")
        html_ptr.write("            <th colspan='8' class='text-center'><h4>Project Summaries</h4></th>\n") 
        html_ptr.write("        </tr>\n") 
        html_ptr.write("    </thead>\n")
        html_ptr.write("</table>\n")

        html_ptr.write("<div class='container'>\n")
        html_ptr.write("    <div class='row'>\n")

        html_ptr.write("        <div class='col-sm'>\n")
        html_ptr.write("<h6 class='gray' style='padding-top: 10px;'><center>Project Hierarchy</center></h6>") 
        html_ptr.write("            <div id='project_hierarchy'></div>\n")
        
        html_ptr.write("        </div>\n")
        html_ptr.write("        <div class='col-sm' style='height: %spx;'>\n" %(columnHeight) )
        html_ptr.write("            <div class='col-sm' style='height: %spx'>\n"%(canvasHeight))
        html_ptr.write("               <canvas id='projectVulnerabilities'></canvas>\n")
        html_ptr.write("             </div>\n")
        html_ptr.write("        </div>\n")
        html_ptr.write("    </div>\n")
        html_ptr.write("</div>\n")

        html_ptr.write("<hr class='small'>")






    html_ptr.write("<table id='vulnerabilityData' class='table table-hover table-sm row-border' style='width:90%'>\n")

    html_ptr.write("    <thead>\n")
    html_ptr.write("        <tr>\n")
    if includeAssociatedFiles:
        html_ptr.write("            <th colspan='10' class='text-center'><h4>Vulnerabilities</h4></th>\n") 
    else:
        html_ptr.write("            <th colspan='9' class='text-center'><h4>Vulnerabilities</h4></th>\n") 
    html_ptr.write("        </tr>\n") 
    html_ptr.write("        <tr>\n") 
    html_ptr.write("            <th style='width: 15%' class='text-center'>VULNERABILITY</th>\n") 
    html_ptr.write("            <th style='width: 20%' class='text-center'>COMPONENT</th>\n")
    if cvssVersion == "3.x": 
        html_ptr.write("            <th style='width: 5%; white-space:nowrap !important' class='text-center'>CVSS v3.x</th>\n")
    else:
        html_ptr.write("            <th style='width: 5%; white-space:nowrap !important' class='text-center'>CVSS v2.0</th>\n")
    html_ptr.write("            <th style='width: 5%' class='text-center'>SEVERITY</th>\n")
    if cvssVersion == "3.x": 
        html_ptr.write("            <th style='width: 5%' class='text-center'>CVSS v3.x VECTOR</th>\n")
    else:
        html_ptr.write("            <th style='width: 5%' class='text-center'>CVSS v2 VECTOR</th>\n")
    html_ptr.write("            <th style='width: 5%' class='text-center'>SOURCE</th>\n")
    html_ptr.write("            <th style='width: 5%' class='text-center'>PUBLISHED</th>\n")
    html_ptr.write("            <th style='width: 5%' class='text-center'>LAST MODIFIED</th>\n")
    
    html_ptr.write("            <th style='width: 40%' class='text-center'>DESCRIPTION</th>\n") 
    if includeAssociatedFiles:
        html_ptr.write("            <th style='width: 40%' class='text-center'>ASSOCIATED FILES</th>\n") 
    html_ptr.write("        </tr>\n")
    html_ptr.write("    </thead>\n")  
    html_ptr.write("    <tbody>\n")  

    for vulnerability in vulnerabilityDetails:

        vulnerabilityDescription = vulnerabilityDetails[vulnerability]["vulnerabilityDescription"]
        # Just in case there are any "tags" that need to be cleaned up
        vulnerabilityDescription = vulnerabilityDescription.replace('<', '&lt').replace('>', '&gt')

        vulnerabilitySource = vulnerabilityDetails[vulnerability]["vulnerabilitySource"]
        vulnerabilityUrl = vulnerabilityDetails[vulnerability]["vulnerabilityUrl"]
        vulnerabilitySeverity = vulnerabilityDetails[vulnerability]["vulnerabilitySeverity"]
        vulnerabilityVector = vulnerabilityDetails[vulnerability]["vulnerabilityVector"]
        vulnerabilityVectorLink = vulnerabilityDetails[vulnerability]["vulnerabilityVectorLink"]
        vulnerabilityScore = vulnerabilityDetails[vulnerability]["vulnerabilityScore"]
        publishedDate = vulnerabilityDetails[vulnerability]["publishedDate"]
        modifiedDate = vulnerabilityDetails[vulnerability]["modifiedDate"]

        if vulnerabilityScore == "N/A":
                vulnerabilityScore = "-"

        html_ptr.write("<td style=\"vertical-align:middle\"><a href=\"%s\" target=\"_blank\">%s</a></td>\n" %(vulnerabilityUrl, vulnerability))


        affectedComponents = vulnerabilityDetails[vulnerability]["affectedComponents"]
        
        
        html_ptr.write("<td style=\"vertical-align:middle\">")
       
        # sort by componentName and then version
        for affectedComponent in sorted(affectedComponents, key=lambda x: (x[1], x[2])):
            inventoryID = affectedComponent[0]
            componentName = affectedComponent[1]
            componentVersionName = affectedComponent[2]
            projectName = affectedComponent[3]
            projectLink = affectedComponent[4]
            inventoryItemLink = affectedComponent[5]

            if includeAssociatedFiles:
                associatedFiles = "\n".join(affectedComponent[6])
            
            html_ptr.write("<a href=\"%s\" target=\"_blank\">%s - %s</a>\n" %(inventoryItemLink, componentName, componentVersionName))
            html_ptr.write("<a href=\"%s\" target=\"_blank\">  (%s)</a><br>\n" %(projectLink, projectName)) 
        
        html_ptr.write("</td>\n")

        html_ptr.write("<td style=\"vertical-align:middle\" class='text-center' data-order=\"%s\"> <span class=\"btn btn-%s\">%s</span></td>\n" %(vulnerabilityScore, vulnerabilitySeverity.lower(), vulnerabilityScore))
        html_ptr.write("<td style=\"vertical-align:middle\">%s</td>\n" %vulnerabilitySeverity)

        if vulnerabilityVectorLink:
            html_ptr.write("<td style=\"vertical-align:middle\"><a href=\"%s\" target=\"_blank\">%s</a></td>\n" %(vulnerabilityVectorLink, vulnerabilityVector))
        else:
            html_ptr.write("<td style=\"vertical-align:middle\">%s</td>\n" %vulnerabilityVector)

        
        html_ptr.write("<td style=\"vertical-align:middle\">%s</td>\n" %vulnerabilitySource)
        html_ptr.write("<td style=\"vertical-align:middle\">%s</td>\n" %publishedDate)
        html_ptr.write("<td style=\"vertical-align:middle\">%s</td>\n" %modifiedDate)
        html_ptr.write("<td style=\"vertical-align:middle\">%s</td>\n" %vulnerabilityDescription)
        
        if includeAssociatedFiles:
            html_ptr.write("<td style=\"vertical-align:middle\">%s</td>\n" %associatedFiles)

        html_ptr.write("</tr>\n")


    html_ptr.write("    </tbody>\n")


    html_ptr.write("</table>\n")  

    html_ptr.write("<!-- END BODY -->\n")  

    #---------------------------------------------------------------------------------------------------
    # Report Footer
    #---------------------------------------------------------------------------------------------------
    html_ptr.write("<!-- BEGIN FOOTER -->\n")
    html_ptr.write("<div class='report-footer'>\n")
    html_ptr.write("  <div style='float:left'>&copy; %s Flexera</div>\n" %fileNameTimeStamp[0:4])
    html_ptr.write("  <div style='float:right'>Generated on %s</div>\n" %now)
    html_ptr.write("<br>\n")
    html_ptr.write("  <div style='float:right'>Report Version: %s</div>\n" %_version.__version__)
    html_ptr.write("</div>\n")
    html_ptr.write("<!-- END FOOTER -->\n")   

    html_ptr.write("</div>\n")

    #---------------------------------------------------------------------------------------------------
    # Add javascript 
    #---------------------------------------------------------------------------------------------------

    html_ptr.write('''

    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js" integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous"></script>
    <script src="https://cdn.datatables.net/1.10.21/js/jquery.dataTables.min.js"></script>  
    <script src="https://cdn.datatables.net/1.10.21/js/dataTables.bootstrap4.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@2.8.0"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jstree/3.3.10/jstree.min.js"></script> 
    ''')

    html_ptr.write("<script>\n")

    html_ptr.write('''

            $(document).ready(function (){
                var table = $('#vulnerabilityData').DataTable({
                    "order": [[ 2, "desc" ]],
                    "lengthMenu": [ [25, 50, 100, -1], [25, 50, 100, "All"] ],
                });
            });
        ''')
    
    # Add the common chartjs config
    add_default_chart_options(html_ptr)
    # Add the js for the application summary stacked bar charts
    generate_application_summary_chart(html_ptr, applicationSummaryData)

    if len(projectList) > 1:
        # Add the js for the project summary stacked bar charts
        generate_project_hierarchy_tree(html_ptr, projectList)
        # Add the js for the project summary stacked bar charts
        generate_project_summary_charts(html_ptr, projectSummaryData)



    html_ptr.write("</script>\n")

    html_ptr.write("</body>\n") 
    html_ptr.write("</html>\n") 
    html_ptr.close() 

    logger.info("    Exiting generate_html_report")
    return htmlFile


####################################################################
def encodeImage(imageFile):

    #############################################
    # Create base64 variable for branding image
    try:
        with open(imageFile,"rb") as image:
            logger.debug("Encoding image: %s" %imageFile)
            encodedImage = base64.b64encode(image.read())
            return encodedImage
    except:
        logger.error("Unable to open %s" %imageFile)
        raise

#----------------------------------------------------------------------------------------#
def add_default_chart_options(html_ptr):
    # Add commont defaults for display charts
    html_ptr.write('''  
        var defaultBarChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        layout: {
            padding: {
                bottom: 25  //set that fits the best
            }
        },
        tooltips: {
            enabled: true,
            yAlign: 'center'
        },
        title: {
            display: true,
            fontColor: "#323E48"
        },

        scales: {
            xAxes: [{
                ticks: {
                    beginAtZero:true,
                    fontSize:11,
                    fontColor: "#323E48",
                    precision:0

                },
                scaleLabel:{
                    display:false
                },
                gridLines: {
                }, 
                stacked: true
            }],
            yAxes: [{
                gridLines: {
                    display:false,
                    color: "#fff",
                    zeroLineColor: "#fff",
                    zeroLineWidth: 0,
                    fontColor: "#323E48"
                },
                ticks: {
                    fontSize:11,
                    fontColor: "#323E48"
                },

                stacked: true
            }]
        },
        legend:{
            display:false
        },
        
    };  ''')

#----------------------------------------------------------------------------------------#
def generate_application_summary_chart(html_ptr, applicationSummaryData):
    logger.info("Entering generate_application_summary_chart")

    cvssVersion = applicationSummaryData["cvssVersion"]
   
    html_ptr.write(''' 
    
    var applicationVulnerabilities= document.getElementById("applicationVulnerabilities");
    var applicationVulnerabilityChart = new Chart(applicationVulnerabilities, {
        type: 'horizontalBar',
        data: {
            datasets: [''')

    if cvssVersion == "3.x":
        html_ptr.write(''' {       
                // Critical Vulnerabilities
                label: 'Critical',
                data: [%s],
                backgroundColor: "#400000"
                },''' %applicationSummaryData["numCriticalVulnerabilities"])      

    html_ptr.write('''   
            {
                // High Vulnerabilities
                label: 'High',
                data: [%s],
                backgroundColor: "#C00000"
            },{
                // Medium Vulnerabilities
                label: 'Medium',
                data: [%s],
                backgroundColor: "#FFA500"
            },{
                // Low Vulnerabilities
                label: 'Low',
                data: [%s],
                backgroundColor: "#FFFF00"
            },{
                // N/A Vulnerabilities
                label: 'N/A',
                data: [%s],
                backgroundColor: "#D3D3D3"
            },
            ]
        },

        options: defaultBarChartOptions,
        
    });

    applicationVulnerabilityChart.options.tooltips.titleFontSize = 0
    
    ''' %(applicationSummaryData["numHighVulnerabilities"], applicationSummaryData["numMediumVulnerabilities"], applicationSummaryData["numLowVulnerabilities"], applicationSummaryData["numNoneVulnerabilities"]) )
    

#----------------------------------------------------------------------------------------#
def generate_project_hierarchy_tree(html_ptr, projectHierarchy):
    logger.info("Entering generate_project_hierarchy_tree")

    html_ptr.write('''var hierarchy = [\n''')

    for project in projectHierarchy:

        html_ptr.write('''{
            'id': '%s', 
            'parent': '%s', 
            'text': '%s',
            'a_attr': {
                'href': '%s'
            }
        },\n'''  %(project["projectID"], project["parent"], project["projectName"], project["projectLink"]))

    html_ptr.write('''\n]''')

    html_ptr.write('''

        $('#project_hierarchy').jstree({ 'core' : {
            'data' : hierarchy
        } });

        $('#project_hierarchy').on('ready.jstree', function() {
            $("#project_hierarchy").jstree("open_all");               

        $("#project_hierarchy").on("click", ".jstree-anchor", function(evt)
        {
            var link = $(evt.target).attr("href");
            window.open(link, '_blank');
        });


        });

    ''' )


#----------------------------------------------------------------------------------------#
def generate_project_summary_charts(html_ptr, projectSummaryData):
    logger.info("Entering generate_project_summary_charts")
    cvssVersion = projectSummaryData["cvssVersion"]

    html_ptr.write(''' 
    
    var projectVulnerabilities= document.getElementById("projectVulnerabilities");
    var projectVulnerabilityChart = new Chart(projectVulnerabilities, {
        type: 'horizontalBar',
        data: {
            labels: %s,
            datasets: [''' %projectSummaryData["projectNames"])

    if cvssVersion == "3.x":
        html_ptr.write('''{          
                // Critical Vulnerabilities
                label: 'Critical',
                data: %s,
                backgroundColor: "#400000"
            },''' %projectSummaryData["numCriticalVulnerabilities"])
    html_ptr.write('''{
                // High Vulnerabilities
                label: 'High',
                data: %s,
                backgroundColor: "#C00000"
            },{
                // Medium Vulnerabilities
                label: 'Medium',
                data: %s,
                backgroundColor: "#FFA500"
            },{
                // Low Vulnerabilities
                label: 'Low',
                data: %s,
                backgroundColor: "#FFFF00"
            },{
                // N/A Vulnerabilities
                label: 'N/A',
                data: %s,
                backgroundColor: "#D3D3D3"
            },
            ]
        },

        options: defaultBarChartOptions,
        
    });
    projectVulnerabilityChart.options.title.text = "Vulnerability Summary"
    
    
    ''' %( projectSummaryData["numHighVulnerabilities"], projectSummaryData["numMediumVulnerabilities"], projectSummaryData["numLowVulnerabilities"], projectSummaryData["numNoneVulnerabilities"]) )
    