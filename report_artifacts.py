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

logger = logging.getLogger(__name__)

#--------------------------------------------------------------------------------#
def create_report_artifacts(reportData):
    logger.info("Entering create_report_artifacts")

    # Dict to hold the complete list of reports
    reports = {}

    htmlFile = generate_html_report(reportData)
    
    reports["viewable"] = htmlFile
    reports["allFormats"] = [htmlFile]

    logger.info("Exiting create_report_artifacts")
    
    return reports 


#------------------------------------------------------------------#
def generate_html_report(reportData):
    logger.info("    Entering generate_html_report")

    reportName = reportData["reportName"]
    projectName  = reportData["projectName"]
    inventoryData = reportData["inventoryData"]
    
    scriptDirectory = os.path.dirname(os.path.realpath(__file__))
    cssFile =  os.path.join(scriptDirectory, "html-assets/css/revenera_common.css")
    logoImageFile =  os.path.join(scriptDirectory, "html-assets/images/logo.svg")
    iconFile =  os.path.join(scriptDirectory, "html-assets/images/favicon-revenera.ico")
    logger.debug("cssFile: %s" %cssFile)
    logger.debug("imageFile: %s" %logoImageFile)
    logger.debug("iconFile: %s" %iconFile)


    #########################################################
    #  Encode the image files
    encodedLogoImage = encodeImage(logoImageFile)
    encodedfaviconImage = encodeImage(iconFile)

    # Grab the current date/time for report date stamp
    now = datetime.now().strftime("%B %d, %Y at %H:%M:%S")

    htmlFile = reportName + ".html"
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
    # Create a common top banner
    #---------------------------------------------------------------------------------------------------
    # Put the image and date in a table for organizational purposes

    html_ptr.write("<!-- BEGIN HEADER -->\n")
    html_ptr.write("<div style='height:35px;'>\n")
    html_ptr.write("    <div style='float:left;'>\n")
    html_ptr.write("    	<img src='data:image/svg+xml;base64,{}' style='width: 400px;'>\n".format(encodedLogoImage.decode('utf-8')))
    html_ptr.write("    </div>\n")
    html_ptr.write("    <div style='float:right' class='report-title'>\n")
    html_ptr.write("         %s\n" %reportName.upper()) 
    html_ptr.write("    </div>\n")
    html_ptr.write("</div>\n")
    html_ptr.write("        <p>\n")  
    html_ptr.write("        <hr class='small'>\n")
    html_ptr.write("<!-- END HEADER -->\n")

    #---------------------------------------------------------------------------------------------------
    # Body of Report
    #---------------------------------------------------------------------------------------------------
    html_ptr.write("<!-- BEGIN BODY -->\n")  

    html_ptr.write("<table id='inventoryData' class='table table-hover table-bordered table-sm' style='width:90%'>\n")

    html_ptr.write("    <thead>\n")
    html_ptr.write("        <tr>\n")
    html_ptr.write("            <th colspan='6' class='text-center'><h4>%s</h4></th>\n" %projectName) 
    html_ptr.write("        </tr>\n") 
    html_ptr.write("        <tr>\n") 
    html_ptr.write("            <th style='width: 30%' class='text-center'>INVENTORY ITEM</th>\n") 
    html_ptr.write("            <th style='width: 10%' class='text-center'>PRIORITY</th>\n") 
    html_ptr.write("            <th style='width: 15%' class='text-center'>COMPONENT</th>\n")
    html_ptr.write("            <th style='width: 10%' class='text-center'>VERSION</th>\n")
    html_ptr.write("            <th style='width: 15%' class='text-center'>LICENSE</th>\n") 
    html_ptr.write("            <th style='width: 18%' class='text-center'>VULNERABILITIES</th>\n")
    html_ptr.write("        </tr>\n")
    html_ptr.write("    </thead>\n")  
    html_ptr.write("    <tbody>\n")  


    ######################################################
    # Cycle through the inventory to create the 
    # table with the results
    for inventoryItem in sorted(inventoryData):
        componentName = inventoryData[inventoryItem]["componentName"]
        componentVersionName = inventoryData[inventoryItem]["componentVersionName"]
        priority = inventoryData[inventoryItem]["priority"]
        selectedLicenseName = inventoryData[inventoryItem]["selectedLicenseName"]
        selectedLicensePriority = inventoryData[inventoryItem]["selectedLicensePriority"]
        vulnerabilityData = inventoryData[inventoryItem]["vulnerabilityData"]

        logger.debug("Reporting for inventory item %s" %inventoryItem)

        numCriticalVulnerabilities = 0
        numHighVulnerabilities = 0
        numMediumVulnerabilities = 0
        numLowVulnerabilities = 0
        numNoneVulnerabilities = 0

        try:
            numCriticalVulnerabilities = vulnerabilityData["numCriticalVulnerabilities"]
            numHighVulnerabilities = vulnerabilityData["numHighVulnerabilities"]
            numMediumVulnerabilities = vulnerabilityData["numMediumVulnerabilities"]
            numLowVulnerabilities = vulnerabilityData["numLowVulnerabilities"]
            numNoneVulnerabilities = vulnerabilityData["numNoneVulnerabilities"]
        except:
            logger.debug("    No vulnerability data")

        html_ptr.write("        <tr> \n")
        html_ptr.write("            <td class='text-left'>%s</td>\n" %(inventoryItem))

        if priority == "High":
            html_ptr.write("            <td data-sort='3' class='text-left'><span class='dot dot-red'></span>P1 - %s</td>\n" %(priority))
        elif priority == "Medium":
            html_ptr.write("            <td data-sort='2' class='text-left'><span class='dot dot-yellow'></span>P2 - %s</td>\n" %(priority))
        elif priority == "Low":
            html_ptr.write("            <td data-sort='1' class='text-left'><span class='dot dot-green'></span>P3 - %s</td>\n" %(priority))
        elif priority == "Other":
            html_ptr.write("            <td data-sort='1' class='text-left'><span class='dot dot-blue'></span>P4 - %s</td>\n" %(priority))
        else:
            html_ptr.write("            <td class='text-left'><span class='dot dot-gray'></span>%s</td>\n" %(priority))

        
        html_ptr.write("            <td class='text-left'>%s</td>\n" %(componentName))
        html_ptr.write("            <td class='text-left'>%s</td>\n" %(componentVersionName))
        html_ptr.write("            <td class='text-left'>%s</td>\n" %(selectedLicenseName))
        html_ptr.write("            <td class='text-center text-nowrap' data-sort='%s' >\n" %numCriticalVulnerabilities)
        
        # Write in single line to remove spaces between btn spans
        html_ptr.write("                <span class='btn btn-critical'>%s</span><span class='btn btn-high'>%s</span><span class='btn btn-medium'>%s</span><span class='btn btn-low'>%s</span><span class='btn btn-none'>%s</span>\n" %(numCriticalVulnerabilities,numHighVulnerabilities,numMediumVulnerabilities, numLowVulnerabilities, numNoneVulnerabilities))

        html_ptr.write("            </td>\n")

        html_ptr.write("        </tr>\n") 
    html_ptr.write("    </tbody>\n")


    html_ptr.write("</table>\n")  

    html_ptr.write("<!-- END BODY -->\n")  

    #---------------------------------------------------------------------------------------------------
    # Report Footer
    #---------------------------------------------------------------------------------------------------
    html_ptr.write("<!-- BEGIN FOOTER -->\n")  
    html_ptr.write("<hr class='small'>\n") 
    html_ptr.write("<div class='report-footer' style=\"height:35px;\">\n")
    html_ptr.write("    <div style=\"float:left\">\n")
    html_ptr.write("        &copy; 2020 Revenera.\n")
    html_ptr.write("    </div>\n")
    html_ptr.write("    <div style=\"float:right\">\n")
    html_ptr.write("        Generated on %s\n" %now)
    html_ptr.write("    </div> \n")
    html_ptr.write("</div> \n")
    html_ptr.write("<!-- END FOOTER -->\n")  

    html_ptr.write("</div>\n")

    #---------------------------------------------------------------------------------------------------
    # Add javascript 
    #---------------------------------------------------------------------------------------------------

    html_ptr.write('''

    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js" integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous"></script>
    <script src="https://cdn.datatables.net/1.10.21/js/jquery.dataTables.min.js"></script>  
    <script src="https://cdn.datatables.net/1.10.21/js/dataTables.bootstrap4.min.js"></script> 
    ''')


    html_ptr.write('''
        <script>
            var table = $('#inventoryData').DataTable();

            $(document).ready(function() {
                table;
            } );
            
        </script>


        ''')


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