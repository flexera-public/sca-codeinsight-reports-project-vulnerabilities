#!/bin/bash
projectId=$1
reportId=$2
authToken=$3
# These are not currently passed via the framework but should be in a future release
domainName=localhost
port=8888

###############################################################################
#  Call the script to collect the data and generate the report
#  This script will create a zip file containing the viewable file
#  combined with another zip file that contains all report artifacts for
#  download.  Since this is executed from the tomcat/bin directory we need to
#  use REPORTDIR to get the location of this shell script since the script is
#  relative to that.
###############################################################################

REPORTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

python3 ${REPORTDIR}/create_report.py -pid $projectId -rid $reportId -authToken $authToken -domainName $domainName -port $port
