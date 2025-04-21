Feature: Set up the deployment secrets

    As a Gaia-X user I want to define a set of deployment secrets (e.g. provider API Keys, predefine SSH keys, 
    potential encryption tokens), which I will be able to attach to different deployment projects.

    Note: the Feature and scenarios are described from user perspective using the GUI. 

Scenario: Set up a secret
Given a web interface in portal that can store secrets in LCM Engine database    
When a user opens the "Add secret" option
And enter the Secret name
And enter the Secret path (e.g. /root/.ssh/authorized_keys)
And enter the permisions parameters for the secret parameter (UID/GUI/mode)
And enter the content of the secret
Then the secret is saved
And secret can be seen on the portal only as a hash (cannot be copied back)
