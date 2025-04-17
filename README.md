This script allows you to scrape a Jira Cloud site using the REST API to capture details about configuration and usage.

To run:
1. Ensure Python3 is installed
2. Install the requests package using pip: https://pypi.org/project/requests/
3. Create a file titled ".env", and insert your email and Atlassian token in the below format:

{ 
    "user" : "YOUR_EMAIL_HERE",
    "token" : "YOUR_TOKEN_HERE"
}

4. Run "python3 jira_discovery.py"