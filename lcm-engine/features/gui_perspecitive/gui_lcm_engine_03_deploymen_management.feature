Feature: Deployment Management

    As a user, I want to manage my deployments and retrieve the status.

    Note: the Feature and scenarios are described from user perspective using the GUI. 

Scenario: Open Manage project Dashboard
Given the infrastructure or application is deployed.
When user clicks "Manage project"
Then A project dashoboard is open where basic project status info and deployment operations are available

Scenario: Get status
Given the "Manage project dashboard" is opened 
When user invokes the "stdout" or "stderr" of any "operation" (e.g. deploy, update, undeploy) 
Then the corresponding standard outputs are shown to the user unveiling the details of the operations

Scenario: Update
Given the "Manage project dashboard" is opened 
And project is deployed
When user adds new input data 
And invokes "Update"
Then orchestrator starts updating procedure

Scenario: Undeploy (or Delete)
Given the "Manage project dashboard" is opened 
And project is deployed
When user invokes "Undeploy"
Then orchestrator starts undeploying procedure
