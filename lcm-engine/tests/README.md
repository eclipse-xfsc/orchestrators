# Gaia-X Orchestration

## Install and Configure VSCode Extension

Acceptance tests are written to work with [vscode extension for making REST API requests](https://marketplace.visualstudio.com/items?itemName=humao.rest-client). Install this REST client extension from the VSCode marketplace.

To configure it, in the workspace or user settings specify the LCM Engine endpoint and default headers. Most API calls require information about a user, which is specified in the `X-Forwarded-User` HTTP header.

```json
"rest-client.defaultHeaders": {
    "User-Agent": "vscode-restclient",
    "X-Forwarded-User": "demo.user@xlab.si",
    "Content-Type": "application/json"
},

"rest-client.environmentVariables": {
    "lcm-engine": {
        "lcm_host": "https://lcm-engine.endpoint.example.com"
    }
}
```

Open a file with `.http` or `.rest` extension and make sure to switch the REST client environment to *lcm-engine* so that the environment variables defined for this environment take place (in our case, the variable `lcm_host`).
