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
def gatherProjectDetails(projectDetails):
    isLast = False
    index = 0
    while(not isLast):
        params = {"startAt" : index}
        response = requests.get(f"{prefix}/project/search", params=params, auth=auth).json()
        index += 50
        isLast = response["isLast"]

        projects = response["values"]
        for project in projects:
            projectKey = project["key"]
            projectDetails[projectKey] = getIndividualProjectDetails(projectKey=projectKey)
            projectDetails[projectKey]["id"] = project["id"]
        # todo: get workflow schemes per project

def getIndividualProjectDetails(projectKey):
    jql = f"project%20%3D%20\"{projectKey}\"%20ORDER%20BY%20updated%20DESC"
    params = {"maxResults" : "1", "fields" : "updated", "jql" : jql}
    response = requests.get(f"{prefix}/search", params=params, auth=auth)
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



def associateProjectsWithScheme(projectDetails, schemeType, schemeName, associatedProjects):
    for project in associatedProjects["values"]:
        key = project["key"]
        if key in projectDetails:
            projectDetails[key][schemeType] = schemeName

def getProjectSchemes(projectDetails, schemeType):
    isLast = False
    index = 0
    while(not isLast):
        params = {"startAt" : index, "expand" : "projects"}
        response = requests.get(f"{prefix}/{schemeType}", params=params, auth=auth).json()

        index += 50
        isLast = response["isLast"]

        schemes = response["values"]
        for schemeDetails in schemes:
            schemeName = schemeDetails["name"]
            associatedProjects = schemeDetails["projects"]
            associateProjectsWithScheme(projectDetails, schemeType, schemeName, associatedProjects)


def getAllProjectSchemes(projectDetails, schemes):
    for scheme in schemes:
        getProjectSchemes(projectDetails, scheme)

# run
projectDetails = {}

gatherProjectDetails(projectDetails)

# not supported: "notificationscheme", "screenscheme", "workflowscheme", "issuesecurityschemes"
schemes = ["issuetypescheme", "issuetypescreenscheme", "priorityscheme"]

getAllProjectSchemes(projectDetails, schemes)

with open("output.json", "w") as f:
    f.write(json.dumps(projectDetails))