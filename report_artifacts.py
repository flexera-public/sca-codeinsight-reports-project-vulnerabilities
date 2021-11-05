'''
Copyright 2020 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Fri Aug 07 2020
File : report_artifacts.py
'''

import logging

import report_artifacts_html
import report_artifacts_xlsx



logger = logging.getLogger(__name__)

#--------------------------------------------------------------------------------#
def create_report_artifacts(reportData):
    logger.info("Entering create_report_artifacts")

    # Dict to hold the complete list of reports
    reports = {}

    htmlFile = report_artifacts_html.generate_html_report(reportData)
    xlsxFile = report_artifacts_xlsx.generate_xlsx_report(reportData)
    
    reports["viewable"] = htmlFile
    reports["allFormats"] = [htmlFile, xlsxFile]

    logger.info("Exiting create_report_artifacts")
    
    return reports 



