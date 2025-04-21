Feature: Deploy application with the Gaia-X (Orchestration) LCM Engine

    As a Gaia-X user, I want to Deploy application with the orchestrator. I want to use the portal to select the application, 
    find if target Infrastructure as a Code (IaC) language exist and, when filling out the required inputs, initiate the deployment
    with sending the instructions to the LCM Engine. 

    Note: the Feature and scenarios are described from user perspective using the GUI. 
            

Scenario: create deployment environment
Given a service template - IaC - for the application and the registered API key for the specific provider
When user select "create a deployment project"
And  sets up a name and given IaC, 
And choses LCM Service
Then LCM Engine creates a new container for specific LCM Service 
And mounts (copies in) in the secrets (e.g. provider API Keys, predefine SSH keys, potential encryption tokens) in the container. 
And If there are more LCM Service dependent requirements, they are installed.
    
Scenario: Deploy service
Given a deployment environment is created (== IaC is prepared and LCM Service is ready and API Keys are prepared )
When user clicks "Deploy" in "Portal" 
Then Application deployment is initiated.

Scenario: Deploy is in progress
Given The "service deploy" has been initiated
When user opens the dashboard of the deployment project
Then user can obtain the current deployment progress accessing the log

Scenario: Deploy is successful
Given The "service deploy" has successfully finished
When user has the deployment project dashboard opened
Then user can obtain the success info
And deployment output parameters defined in IaC, such as IPs or URL where the application can be accessed.


