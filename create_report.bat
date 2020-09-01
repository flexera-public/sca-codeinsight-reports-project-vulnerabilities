
@echo off
set projectId=%1
set reportId=%2
set authToken=%3
rem # These are not currently passed via the framework but should be in a future release
set domainName="localhost"
set port=8888

rem ###############################################################################
rem #  Call the script to collect the data and generate the report
rem #  This script will create a zip file containing the viewable file
rem #  combined with another zip file that contains all report artifacts for 
rem #  download.  Since this is executed from the tomcat/bin directory we need to 
rem #  use ~dp0 to get the location of this batch file since the script is
rem #  relative to that.
rem ###############################################################################

python %~dp0\create_report.py -pid %projectId% -rid %reportId% -authToken %authToken% -domainName %domainName% -port %port%
