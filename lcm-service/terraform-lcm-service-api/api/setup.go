package api

import (
	"context"
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/hashicorp/go-version"
	"github.com/hashicorp/hc-install/product"
	"github.com/hashicorp/hc-install/releases"
	"github.com/hashicorp/terraform-exec/tfexec"
	log "github.com/sirupsen/logrus"
	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"
	_ "gitlab.com/gaia-x/data-infrastructure-federation-services/orc/lcm-service/terraform-lcm-service-api/docs"
	"net/http"
	"os"
	"strconv"
)

// getEnvWithAlternativeStr retrieves the value of environment variable or  returns the provided string alternative
func getEnvWithAlternativeStr(key string, alternative string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return alternative
}

// getCurrentWorkingDirectory retrieves current working directory
func getCurrentWorkingDirectory() string {
	workdir, err := os.Getwd()
	if err != nil {
		log.Fatal(fmt.Sprintf("error getting working directory: %s", err))
	}

	return workdir
}

// SetupApiConfiguration configures and returns API settings (sets vars by reading environment variables)
func SetupApiConfiguration() Configuration {
	var workingDirectory = ""
	value, ok := os.LookupEnv("TERRAFORM_API_WORKDIR")
	if ok {
		workingDirectory = value
		dir, err := os.Stat(value)
		if err != nil {
			log.Error(fmt.Sprintf("failed to open directory %s, error: %s", workingDirectory, err))
			workingDirectory = getCurrentWorkingDirectory()
		} else if !dir.IsDir() {
			log.Error(fmt.Sprintf("%q is not a directory", dir.Name()))
			workingDirectory = getCurrentWorkingDirectory()
		}
	} else {
		workingDirectory = getCurrentWorkingDirectory()
	}

	var apiDebugMode = false
	value, ok = os.LookupEnv("TERRAFORM_API_DEBUG_MODE")
	if ok {
		valueBool, err := strconv.ParseBool(value)
		if err != nil {
			log.Error(fmt.Sprintf("failed to convert value %s to bool, error: %s", value, err))
		} else {
			apiDebugMode = valueBool
		}
	}

	return Configuration{
		Version:          getEnvWithAlternativeStr("TERRAFORM_API_VERSION", "latest"),
		TerraformVersion: getEnvWithAlternativeStr("TERRAFORM_API_TERRAFORM_VERSION", "1.3.4"),
		WorkingDirectory: workingDirectory,
		DebugMode:        apiDebugMode,
		Port:             getEnvWithAlternativeStr("TERRAFORM_API_TERRAFORM_VERSION", "8080"),
		SwaggerUrl:       getEnvWithAlternativeStr("TERRAFORM_API_TERRAFORM_VERSION", "swagger"),
		TrustedProxy:     getEnvWithAlternativeStr("TERRAFORM_API_TERRAFORM_VERSION", ""),
	}
}

// SetupTerraform installs Terraform and initializes Terraform struct object
func SetupTerraform(ctx context.Context, terraformVersion, workingDir string) (*tfexec.Terraform, error) {
	installer := &releases.ExactVersion{
		Product: product.Terraform,
		Version: version.Must(version.NewVersion(terraformVersion)),
	}

	execPath, err := installer.Install(ctx)
	if err != nil {
		return nil, fmt.Errorf("installing Terraform: %w", err)
	}

	tf, err := tfexec.NewTerraform(workingDir, execPath)
	if err != nil {
		return nil, fmt.Errorf("creating tfexec.Terraform obj: %w", err)
	}

	// TODO: maybe attach stdout and stderr to an io.Writer to capture the outputs
	// (e.g. Terraform apply, Terraform plan, Terraform destroy output)
	// e.g:
	// var outBuf *bytes.Buffer
	// var errBuf *bytes.Buffer
	// tf.SetStdout(outBuf)
	// tf.SetStderr(errBuf)

	return tf, nil
}

// SetupRouter initializes an API Router for production
func SetupRouter(api Api) (*gin.Engine, error) {
	// init API
	router := gin.Default()

	// set API routes
	router.POST("/init", api.InitHandler)
	router.POST("/validate", api.ValidateHandler)
	router.POST("/plan", api.PlanHandler)
	router.POST("/apply", api.ApplyHandler)
	router.POST("/destroy", api.DestroyHandler)
	router.POST("/fmt", api.FmtHandler)
	router.POST("/force-unlock", api.ForceUnlockHandler)
	router.POST("/get", api.GetHandler)
	router.POST("/graph", api.GraphHandler)
	router.POST("/import", api.ImportHandler)
	router.GET("/output", api.OutputHandler)
	router.GET("/providers/schema", api.ProvidersSchemaHandler)
	router.POST("/providers/lock", api.ProvidersLockHandler)
	router.GET("/show", api.ShowHandler)
	router.DELETE("/state/rm", api.StateRmHandler)
	router.POST("/state/mv", api.StateMvHandler)
	router.DELETE("/untaint", api.UntaintHandler)
	router.GET("/version", api.VersionHandler)
	router.GET("/workspace/show", api.WorkspaceShowHandler)
	router.GET("/workspace/list", api.WorkspaceListHandler)
	router.POST("/workspace/select", api.WorkspaceSelectHandler)
	router.POST("/workspace/new", api.WorkspaceNewHandler)
	router.DELETE("/workspace/delete", api.WorkspaceDeleteHandler)

	// serve API docs (Swagger UI) when in debug mode
	if api.Configuration.DebugMode {
		router.GET(fmt.Sprintf("/%s/*any", api.Configuration.SwaggerUrl),
			ginSwagger.WrapHandler(swaggerFiles.Handler),
		)
		router.GET("swagger.json", func(c *gin.Context) {
			c.File("docs/swagger.json")
		})
		router.GET("swagger.yaml", func(c *gin.Context) {
			c.File("docs/swagger.yaml")
		})
		router.GET(fmt.Sprintf("/%s", api.Configuration.SwaggerUrl), func(c *gin.Context) {
			c.Redirect(http.StatusMovedPermanently, fmt.Sprintf("/%s/index.html", api.Configuration.SwaggerUrl))
		})
	}

	// set trusted proxy if needed
	if api.Configuration.TrustedProxy != "" {
		err := router.SetTrustedProxies([]string{api.Configuration.TrustedProxy})
		if err != nil {
			return nil, fmt.Errorf("setting trusted proxy: %w", err)
		}
	}

	return router, nil
}

// SetupApi sets up the API by setting its Configuration, Terraform installation and Router
func SetupApi() (Api, error) {
	// init vars from environment and configure API
	apiConfig := SetupApiConfiguration()
	// init Terraform
	tf, err := SetupTerraform(context.Background(), apiConfig.TerraformVersion, apiConfig.WorkingDirectory)
	if err != nil {
		log.Fatalf("init Terraform: %v", err)
	}
	// create the main API object
	api := Api{Terraform: tf, Configuration: apiConfig}
	// init API Router
	router, err := SetupRouter(api)
	if err != nil {
		log.Fatalf("setup gin Router: %v", err)
	}
	// set API Router
	api.Router = router

	return api, nil
}
