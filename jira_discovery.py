import json
import requests
from requests.auth import HTTPBasicAuth

env = json.loads(open(".env", "r").read())

user = env["user"]
token = env["token"]

prefix = "https://mddeloitte-ja.atlassian.net/rest/api/2"
headers = {"Accept": "application/json"}
auth = HTTPBasicAuth(user, token)

# Part 1 functions
def gatherProjectDetails(projectDetails):
    isLast = False
    index = 0
    while(not isLast):
        params = {"startAt" : index}
        print(f"Getting high-level project details for index {index} to {index + 50}")
        response = requests.get(f"{prefix}/project/search", params=params, auth=auth).json()
        index += 50
        isLast = response["isLast"]

        projects = response["values"]
        for project in projects:
            projectKey = project["key"]
            projectDetails[projectKey] = getIndividualProjectDetails(projectKey=projectKey)
            projectDetails[projectKey]["id"] = project["id"]

    # getWorkflowSchemes(projectDetails)

def getIndividualProjectDetails(projectKey):
    print(f"Getting individual project details for project {projectKey}")
    jql = f"project%20%3D%20\"{projectKey}\"%20ORDER%20BY%20updated%20DESC"
    params = {"maxResults" : "1", "fields" : "updated", "jql" : jql}
    response = requests.get(f"{prefix}/search", params=params, auth=auth)
    details = response.json()
    try:
        issueCount = details["total"]
    except:
        issueCount = 0
    if issueCount == 0:
        lastUpdated = ""
    else:
        lastUpdated = details["issues"][0]["fields"]["updated"]
    return {"issueCount" : issueCount, "lastUpdated" : lastUpdated}

def getWorkflowSchemes(projectDetails):
    for project in projectDetails:
        print(f"Getting workflow scheme for project {project}")
        id = projectDetails[project]["id"]
        params = {"projectId" : id}
        response = requests.get(f"{prefix}/workflowscheme/project", params=params, auth=auth)
        details = response.json()

        workflowScheme = details["values"]
        if(len(workflowScheme) > 0):
            schemeName = workflowScheme[0]["workflowScheme"]["name"]
            projectDetails[project]["workflowscheme"] = schemeName


def associateProjectsWithScheme(projectDetails, schemeType, schemeName, associatedProjects):
    for project in associatedProjects["values"]:
        key = project["key"]
        if key in projectDetails:
            projectDetails[key][schemeType] = schemeName

def getProjectSchemes(projectDetails, schemeType):
    isLast = False
    index = 0
    while(not isLast):
        print(f"Getting projects in scheme {schemeType} at index {index} to {index + 50}")
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

# Part 2 functions
def gatherProjectRoleMappings(projectRoleMappings, projects):
    for project in projects:
            # Todo: https://mddeloitte-ja.atlassian.net/rest/api/2/project/API/role
            print(f"Getting role mappings for project {project}")
            response = requests.get(f"{prefix}/project/{project}/role", auth=auth)
            details = response.json()
            print(details)
            for role in details:
                unpackRole(projectRoleMappings, project, details[role])

def unpackRole(projectRoleMappings, project, url):
    print(f"Unpacking role for project {project} at url {url}")
    response = requests.get(url, auth=auth).json()
    name = response["name"]
    id = response["id"]
    users = []
    for user in response["actors"]:
        users.append({user["id"] : user["displayName"]})
    if project not in projectRoleMappings:
        projectRoleMappings[project] = {id : {"roleName" : name, "users" : users}}
    else:
        projectRoleMappings[project][id] = {"roleName" : name, "users" : users}

# Part 3 functions
def gatherCustomFieldDetails(customFieldDetails):
    isLast = False
    index = 0
    while(not isLast):
        print(f"Getting high-level custom field details for index {index} to {index + 50}")
        params = {"startAt" : index, "expand" : "lastUsed"}
        response = requests.get(f"{prefix}/field/search", params=params, auth=auth).json()
        index += 50
        isLast = response["isLast"]

        for field in response["values"]:
            fieldId = field["id"]
            if "customfield" in fieldId:
                name = field["name"]
                if "value" in field["lastUsed"]:
                    lastUsed = field["lastUsed"]["value"]
                else:
                    lastUsed = ""
                customFieldDetails[fieldId] = {"name": name, "lastUsed" : lastUsed}
    
    getIndividualCustomFieldDetails(customFieldDetails)

def getIndividualCustomFieldDetails(customFieldDetails):
    for customField in customFieldDetails:
        name = customFieldDetails[customField]["name"]
        print(f"Getting individual field details for field {name}")
        jql = f"\"{name}\" IS NOT EMPTY"
        params = {"maxResults" : "1", "fields" : "updated", "jql" : jql}
        response = requests.get(f"{prefix}/search", params=params, auth=auth)
        details = response.json()
        try:
            issueCount = details["total"]
        except:
            issueCount = 0
        customFieldDetails[customField]["issueCount"] = issueCount



# run

# Part 1: Number of Projects with list of schemes per project and last time project was used and number of issues against that project
projectDetails = {}

gatherProjectDetails(projectDetails)

# not supported: "notificationscheme", "screenscheme", "issuesecurityschemes"
schemes = ["issuetypescheme", "issuetypescreenscheme", "priorityscheme"]

getAllProjectSchemes(projectDetails, schemes)

with open("projects.json", "w") as f:
    f.write(json.dumps(projectDetails))


# Part 2: Users/Group to Role mapping per project
projectRoleMappings = {}
#gatherProjectRoleMappings(projectRoleMappings, projectDetails.keys())
gatherProjectRoleMappings(projectRoleMappings, ["API"])

with open("projectrolemappings.json", "w") as f:
    f.write(json.dumps(projectRoleMappings))

# Part 3: Number of custom fields + number of issues used against + last date used
customFieldDetails = {}
gatherCustomFieldDetails(customFieldDetails)

with open("customfields.json", "w") as f:   
    f.write(json.dumps(customFieldDetails))