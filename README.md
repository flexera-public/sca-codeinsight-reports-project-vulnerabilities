
# sca-codeinsight-reports-project-inventory

  

The sca-codeinsight-reports-project-inventory repository is a example report for Revenera's Code Insight product. That allows a user to get a quick high level summary of the inventory items within a project

  
  
  

## Prerequisites

**Minimum Code Insight Release Version**: 2020R3
  

This repository contains two submodules pointing to other git repos for code that can be in common to multiple projects. After the initial clone of sca-codeinsight-reports-project-comparison you will need to enter the cloned directory and link and pull down the necessary code

    git submodule init

    git submodule update

  

## Usage

  

This report is executed directly from within Revenera's Code Insight product. From the summary page of each Code Insight project it is possible to *generate* the **Project Inventory Report** via the Custom Report Framework. Once this report is selected the second project for comparision can be selected

  

The Code Insight Custom Report Framework will provide the following to the custom report when initiated:

  

- Project ID

- Report ID

- Authorization Token

  

For this example report these three items are passed on to a batch or sh file which will in turn execute a python script. This script will then:

  

- Collect data for the report via REST API using the Project ID and Authorization Token

- Take the collected data and

- create a simple html document with details about the project - The *"viewable"* file

- Create a zip file of this html document - The *"downloadable"* file

- Create a zip file with the viewable file and the downloadable file

- Upload this combined zip file to Code Insight via REST API

- Delete the report artifacts that were created as the script ran

  

### Registering the Report

  

Prior to being able to call the script directly from within Code Insight it must be registered. The registration.py file can be used to directly register the report once the contents of this repository have been copied into the custom_report_script folder at the base Code Insight installation directory.

  

To register this report:

python registration.py -reg

  

To unregister this report:

python registration.py -unreg

  

## License

  

[MIT](LICENSE.TXT)