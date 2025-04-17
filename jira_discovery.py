import json
import requests
from requests.auth import HTTPBasicAuth

env = json.loads(open(".env", "r").read())

user = env["user"]
token = env["token"]

prefix = "https://mddeloitte-ja.atlassian.net/rest/api/2"
headers = {"Accept": "application/json"}
auth = HTTPBasicAuth(user, token)

# Functions
def gatherProjectDetails(projects):
    projectDetails = {}
    for project in projects:
        projectKey = project["key"]
        projectDetails[projectKey] = getIndividualProjectDetails(projectKey=projectKey)
    return projectDetails

def getIndividualProjectDetails(projectKey):
    jql = f"project%20%3D%20\"{projectKey}\"%20ORDER%20BY%20updated%20DESC"
    response = requests.get(f"{prefix}/search?fields=updated&jql={jql}", auth=auth)
    projectDetails = response.json()
    try:
        issueCount = projectDetails["total"]
    except:
        issueCount = 0
    if issueCount == 0:
        lastUpdated = ""
    else:
        lastUpdated = projectDetails["issues"][0]["fields"]["updated"]
    return {"issueCount" : issueCount, "lastUpdated" : lastUpdated}

# Run
response = requests.get(f"{prefix}/project/search", auth=auth)
projectDetails = gatherProjectDetails(response.json()["values"])

with open("output.json", "w") as f:
    f.write(json.dumps(projectDetails))