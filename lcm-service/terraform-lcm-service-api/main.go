package main

import (
	"fmt"

	"github.com/eclipse-xfsc/orchestrators/terraform-lcm-service-api/api"
	"github.com/eclipse-xfsc/orchestrators/terraform-lcm-service-api/docs"
	log "github.com/sirupsen/logrus"
)

// @title        Terraform LCM Service API
// @description  A stateful Terraform API for orchestration environment (single user, single project, single deployment)
// @license.name Mozilla Public License 2.0
// @license.url  https://www.mozilla.org/en-US/MPL/2.0/

// main configures and starts the API
func main() {
	// set up the API
	apiObject, err := api.SetupApi()
	if err != nil {
		log.Fatalf("setup gin router: %v", err)
	}

	// set API version
	docs.SwaggerInfo.Version = apiObject.Configuration.Version

	// run the API
	err = apiObject.Router.Run(":" + apiObject.Configuration.Port)
	if err != nil {
		log.Fatal(fmt.Sprintf("error starting Terraform API: %s", err))
	}
}
