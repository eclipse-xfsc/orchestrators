package api

import (
	"encoding/json"
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/hashicorp/terraform-exec/tfexec"
	"net/http"
)

// InitHandler calls Terraform init command
// @Summary     Prepares your working directory for other commands
// @Description Initializes a working directory containing Terraform Configuration files
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     500 {object} TerraformError
// @Router      /init [post]
func (api Api) InitHandler(ctx *gin.Context) {
	// TODO: add possibility to run Update/Upgrade by specifying a query param (e.g. update=true)
	err := api.Terraform.Init(ctx, tfexec.Upgrade(true))
	if err != nil {
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("init", err))
		return
	}

	ctx.JSON(http.StatusOK, JSONResult{Message: "Terraform has been successfully initialized!"})
}

// ValidateHandler calls Terraform validate command
// @Summary     Checks whether the Configuration is valid
// @Description Validates the Configuration files in a directory
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     500 {object} TerraformError
// @Failure     500 {object} JsonMarshalError
// @Router      /validate [post]
func (api Api) ValidateHandler(ctx *gin.Context) {
	state, err := api.Terraform.Validate(ctx)
	if err != nil {
		if checkIfInitError(ctx, err) {
			return
		}
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("validate", err))
		return
	}

	data, err := json.Marshal(TerraformValidateOutput{*state})
	if err != nil {
		abortCall(ctx, http.StatusInternalServerError, JsonMarshalError{err})
		return
	}

	ctx.JSON(http.StatusOK, JSONResult{Message: "Validate complete!", Data: data})
}

// PlanHandler calls Terraform plan command
// @Summary     Shows changes required by the current Configuration
// @Description Creates an execution plan, which lets you preview the changes for your infrastructure
// @Param       vars      query []string false "Values for input variables, each var supplied as a single string (e,g., 'foo=bar'") collectionFormat(multi)
// @Param       var_files query []string false "Path tfvars file containing values for potentially many input variables"            collectionFormat(multi)
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     400 {object} QueryError
// @Failure     500 {object} TerraformError
// @Failure     500 {object} NeedsInitError
// @Failure     500 {object} JsonMarshalError
// @Router      /plan [post]
func (api Api) PlanHandler(ctx *gin.Context) {
	var queryParams PlanQueryParams
	err := ctx.ShouldBindQuery(&queryParams)
	if err != nil {
		abortCall(ctx, http.StatusBadRequest, QueryError{err})
		return
	}

	var planOpts []tfexec.PlanOption
	for _, variable := range queryParams.Vars {
		planOpts = append(planOpts, tfexec.Var(variable))
	}

	for _, varFile := range queryParams.VarFiles {
		planOpts = append(planOpts, tfexec.VarFile(varFile))
	}

	changed, err := api.Terraform.Plan(ctx, planOpts...)
	if err != nil {
		if checkIfInitError(ctx, err) {
			return
		}
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("plan", err))
		return
	}

	data, err := json.Marshal(TerraformPlanOutput{Changed: changed})
	if err != nil {
		abortCall(ctx, http.StatusInternalServerError, JsonMarshalError{err})
		return
	}

	ctx.JSON(http.StatusOK, JSONResult{Data: data})
}

// ApplyHandler calls Terraform apply command
// @Summary     Create or update infrastructure
// @Description Executes the actions proposed in a Terraform plan
// @Param       refresh_only query bool     false "If true updates the state to match remote systems"
// @Param       replace      query string   false "An address of the resource to be marked as tainted (degraded or damaged object)"
// @Param       vars         query []string false "Values for input variables, each var supplied as a single string (e,g., 'foo=bar')" collectionFormat(multi)
// @Param       var_files    query []string false "Path tfvars file containing values for potentially many input variables"            collectionFormat(multi)
// @Param       parallelism  query int      false "Number of concurrent operation as Terraform walks the graph (default is 10)"        minimum(1)
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     400 {object} QueryError
// @Failure     500 {object} TerraformError
// @Failure     500 {object} NeedsInitError
// @Router      /apply [post]
func (api Api) ApplyHandler(ctx *gin.Context) {
	var queryParams ApplyQueryParams
	err := ctx.ShouldBindQuery(&queryParams)
	if err != nil {
		abortCall(ctx, http.StatusBadRequest, QueryError{err})
		return
	}

	var applyOpts []tfexec.ApplyOption
	applyOpts = append(applyOpts, tfexec.Refresh(queryParams.RefreshOnly))
	if queryParams.Replace != "" {
		applyOpts = append(applyOpts, tfexec.Replace(queryParams.Replace))
	}

	for _, variable := range queryParams.Vars {
		applyOpts = append(applyOpts, tfexec.Var(variable))
	}

	for _, varFile := range queryParams.VarFiles {
		applyOpts = append(applyOpts, tfexec.VarFile(varFile))
	}

	if queryParams.Parallelism != 0 {
		applyOpts = append(applyOpts, tfexec.Parallelism(queryParams.Parallelism))
	}

	err = api.Terraform.Apply(ctx, applyOpts...)
	if err != nil {
		if checkIfInitError(ctx, err) {
			return
		}
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("apply", err))
		return
	}

	ctx.JSON(http.StatusOK, JSONResult{Message: "Apply complete!"})
}

// DestroyHandler calls Terraform destroy command
// @Summary     Destroys previously-created infrastructure
// @Description Destroys all remote objects managed by a particular api.Terraform Configuration
// @Param       vars        query []string false "Values for input variables, each var supplied as a single string (e,g., 'foo=bar'") collectionFormat(multi)
// @Param       var_files   query []string false "Path tfvars file containing values for potentially many input variables"            collectionFormat(multi)
// @Param       parallelism query int      false "Number of concurrent operation as Terraform walks the graph (default is 10)"        minimum(1)
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     500 {object} TerraformError
// @Failure     500 {object} NeedsInitError
// @Router      /destroy [post]
func (api Api) DestroyHandler(ctx *gin.Context) {
	var queryParams DestroyQueryParams
	err := ctx.ShouldBindQuery(&queryParams)
	if err != nil {
		abortCall(ctx, http.StatusBadRequest, QueryError{err})
		return
	}

	var destroyOpts []tfexec.DestroyOption
	for _, variable := range queryParams.Vars {
		destroyOpts = append(destroyOpts, tfexec.Var(variable))
	}

	for _, varFile := range queryParams.VarFiles {
		destroyOpts = append(destroyOpts, tfexec.VarFile(varFile))
	}

	if queryParams.Parallelism != 0 {
		destroyOpts = append(destroyOpts, tfexec.Parallelism(queryParams.Parallelism))
	}

	err = api.Terraform.Destroy(ctx, destroyOpts...)
	if err != nil {
		err = fmt.Errorf("error running destroy: %w", err)
		abortCall(ctx, http.StatusInternalServerError, err)
		return
	}

	ctx.JSON(http.StatusOK, JSONResult{Message: "Destroy complete!"})
}

// FmtHandler calls Terraform fmt command
// @Summary     Reformats your Configuration in the standard style
// @Description Rewrites Terraform Configuration files to a canonical format and style
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     500 {object} TerraformError
// @Failure     500 {object} JsonMarshalError
// @Router      /fmt [post]
func (api Api) FmtHandler(ctx *gin.Context) {
	formatted, changedFiles, err := api.Terraform.FormatCheck(ctx, tfexec.Recursive(true))
	if err != nil {
		err = fmt.Errorf("executing fmt check: %w", err)
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("fmt", err))
		return
	}

	out := TerraformFormatOutput{Formatted: formatted, ChangedFiles: changedFiles}
	data, err := json.Marshal(out)
	if err != nil {
		abortCall(ctx, http.StatusInternalServerError, JsonMarshalError{err})
		return
	}
	if formatted {
		ctx.JSON(http.StatusOK, JSONResult{Message: "config files are already formatted!", Data: data})
		return
	}

	err = api.Terraform.FormatWrite(ctx, tfexec.Recursive(true))
	if err != nil {
		err = fmt.Errorf("executing fmt write: %w", err)
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("fmt", err))
		return
	}

	ctx.JSON(http.StatusOK, JSONResult{Message: "config files got formatted", Data: data})
}

// ForceUnlockHandler calls Terraform force-unlock command
// @Summary     Releases a stuck lock on the current workspace
// @Description Manually unlocks the state for the defined Configuration
// @Param       lock_id query string true "A unique lock id"
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     400 {object} QueryError
// @Failure     500 {object} TerraformError
// @Failure     500 {object} NeedsInitError
// @Router      /force-unlock [post]
func (api Api) ForceUnlockHandler(ctx *gin.Context) {
	var queryParams ForceUnlockQueryParams
	err := ctx.ShouldBindQuery(&queryParams)
	if err != nil {
		abortCall(ctx, http.StatusBadRequest, QueryError{err})
		return
	}

	err = api.Terraform.ForceUnlock(ctx, queryParams.LockId)
	if err != nil {
		if checkIfInitError(ctx, err) {
			return
		}
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("force-unlock", err))
		return
	}

	ctx.JSON(http.StatusOK, JSONResult{Message: "Terraform state has been successfully unlocked!"})
}

// GetHandler calls Terraform get command
// @Summary     Installs or upgrades remote Terraform modules
// @Description Destroys all remote objects managed by a particular Terraform Configuration
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     500 {object} TerraformError
// @Router      /get [post]
func (api Api) GetHandler(ctx *gin.Context) {
	// TODO: add possibility to run Update/Upgrade by specifying a query param (e.g. update=true)
	err := api.Terraform.Get(ctx, tfexec.Update(true))
	if err != nil {
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("get", err))
		return
	}

	ctx.JSON(http.StatusOK, nil)
}

// GraphHandler calls Terraform graph command
// @Summary     Generates a Graphviz graph of the steps in an operation
// @Description Generates a visual representation of either a Configuration or execution plan
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     500 {object} TerraformError
// @Failure     500 {object} NeedsInitError
// @Router      /graph [post]
func (api Api) GraphHandler(ctx *gin.Context) {
	graph, err := api.Terraform.Graph(ctx)
	if err != nil {
		if checkIfInitError(ctx, err) {
			return
		}
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("graph", err))
		return
	}

	data, err := json.Marshal(TerraformGraphOutput{Output: graph})
	ctx.JSON(http.StatusOK, JSONResult{Data: data})
}

// ImportHandler calls Terraform import command
// @Summary     Associates existing infrastructure with a Terraform resource
// @Description Imports existing resources into Terraform
// @Param       address query string true "A valid resource address at which resource will be imported"
// @Param       id      query string true "An existing resource id that will be found by import"
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     400 {object} QueryError
// @Failure     500 {object} TerraformError
// @Failure     500 {object} NeedsInitError
// @Router      /import [post]
func (api Api) ImportHandler(ctx *gin.Context) {
	var queryParams ImportQueryParams
	err := ctx.ShouldBindQuery(&queryParams)
	if err != nil {
		abortCall(ctx, http.StatusBadRequest, QueryError{err})
		return
	}

	err = api.Terraform.Import(ctx, queryParams.Address, queryParams.Id)
	if err != nil {
		if checkIfInitError(ctx, err) {
			return
		}
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("import", err))
		return
	}

	ctx.JSON(http.StatusOK, JSONResult{Message: "Import successful!"})
}

// OutputHandler calls Terraform output command
// @Summary     Shows output values from your root module
// @Description Extracts the value of an output variable from the state file
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     500 {object} TerraformError
// @Failure     500 {object} NeedsInitError
// @Failure     500 {object} JsonMarshalError
// @Router      /output [get]
func (api Api) OutputHandler(ctx *gin.Context) {
	output, err := api.Terraform.Output(ctx)
	if err != nil {
		if checkIfInitError(ctx, err) {
			return
		}
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("output", err))
		return
	}

	out := TerraformOutputOutput{
		Output: output,
	}
	data, err := json.Marshal(out)
	if err != nil {
		abortCall(ctx, http.StatusInternalServerError, JsonMarshalError{err})
		return
	}

	ctx.JSON(http.StatusOK, JSONResult{Data: data})
}

// ProvidersSchemaHandler calls Terraform providers schema command
// @Summary     Shows the providers required for this Configuration
// @Description Prints detailed schemas for the providers used in the current Configuration
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     500 {object} TerraformError
// @Failure     500 {object} NeedsInitError
// @Failure     500 {object} JsonMarshalError
// @Router      /providers/schema [get]
func (api Api) ProvidersSchemaHandler(ctx *gin.Context) {
	providersSchema, err := api.Terraform.ProvidersSchema(ctx)
	if err != nil {
		if checkIfInitError(ctx, err) {
			return
		}
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("providers schema", err))
		return
	}

	out := TerraformProvidersSchemaOutput{*providersSchema}
	data, err := json.Marshal(out)
	if err != nil {
		abortCall(ctx, http.StatusInternalServerError, JsonMarshalError{err})
		return
	}

	ctx.JSON(http.StatusOK, JSONResult{Data: data})
}

// ProvidersLockHandler calls Terraform providers lock command
// @Summary     Updates the dependency lock file to include a selected version for each provider
// @Description Consults upstream registries to write provider dependency information into the dependency lock file
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     500 {object} TerraformError
// @Failure     500 {object} NeedsInitError
// @Router      /providers/lock [post]
func (api Api) ProvidersLockHandler(ctx *gin.Context) {
	err := api.Terraform.ProvidersLock(ctx)
	if err != nil {
		if checkIfInitError(ctx, err) {
			return
		}
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("providers lock", err))
		return
	}

	ctx.JSON(http.StatusOK, JSONResult{Message: "Success! Terraform has updated the lock file."})
}

// ShowHandler calls Terraform show command
// @Summary     Shows the current state or a saved plan
// @Description Provides human-readable output from a state or plan file
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     500 {object} NeedsInitError
// @Failure     500 {object} TerraformError
// @Failure     500 {object} JsonMarshalError
// @Router      /show [get]
func (api Api) ShowHandler(ctx *gin.Context) {
	state, err := api.Terraform.Show(ctx)
	if err != nil {
		if checkIfInitError(ctx, err) {
			return
		}
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("show", err))
		return
	}

	out := TerraformShowOutput{*state}
	data, err := json.Marshal(out)
	if err != nil {
		abortCall(ctx, http.StatusInternalServerError, JsonMarshalError{err})
		return
	}

	ctx.JSON(http.StatusOK, JSONResult{Data: data})
}

// StateRmHandler calls Terraform state rm command
// @Summary     Forgets the resource, while it continues to exist in the remote system
// @Description Removes a binding to an existing remote object without first destroying it
// @Param       address query string true "A valid resource address to be removed from record"
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     400 {object} QueryError
// @Failure     500 {object} TerraformError
// @Failure     500 {object} NeedsInitError
// @Router      /state/rm [delete]
func (api Api) StateRmHandler(ctx *gin.Context) {
	var queryParams StateRmQueryParams
	err := ctx.ShouldBindQuery(&queryParams)
	if err != nil {
		if checkIfInitError(ctx, err) {
			return
		}
		abortCall(ctx, http.StatusBadRequest, QueryError{err})
		return
	}

	err = api.Terraform.StateRm(ctx, queryParams.Address)
	if err != nil {
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("state rm", err))
		return
	}

	ctx.JSON(http.StatusOK, nil)
}

// StateMvHandler calls Terraform state mv command
// @Summary     Moves the remote objects currently associated with the source to be tracked instead by the destination
// @Description Retains an existing remote object but track it as a different resource instance address
// @Param       source      query string true "A valid resource address for source"
// @Param       destination query string true "A valid resource address for destination"
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     400 {object} QueryError
// @Failure     500 {object} TerraformError
// @Failure     500 {object} NeedsInitError
// @Router      /state/mv [post]
func (api Api) StateMvHandler(ctx *gin.Context) {
	var queryParams StateMvQueryParams
	err := ctx.ShouldBindQuery(&queryParams)
	if err != nil {
		if checkIfInitError(ctx, err) {
			return
		}
		abortCall(ctx, http.StatusBadRequest, QueryError{err})
		return
	}

	err = api.Terraform.StateMv(ctx, queryParams.Source, queryParams.Destination)
	if err != nil {
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("state mv", err))
		return
	}

	ctx.JSON(http.StatusOK, nil)
}

// UntaintHandler calls Terraform untaint command
// @Summary     Removes the tainted state from a resource instance
// @Description Removes the taint marker from the object (will not modify remote objects, will modify the state)
// @Param       address query string true "A resource address for particular resource instance which is currently tainted"
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     400 {object} QueryError
// @Failure     500 {object} TerraformError
// @Failure     500 {object} NeedsInitError
// @Router      /untaint [delete]
func (api Api) UntaintHandler(ctx *gin.Context) {
	var queryParams UntaintQueryParams
	err := ctx.ShouldBindQuery(&queryParams)
	if err != nil {
		if checkIfInitError(ctx, err) {
			return
		}
		abortCall(ctx, http.StatusBadRequest, QueryError{err})
		return
	}

	err = api.Terraform.Untaint(ctx, queryParams.Address)
	if err != nil {
		if checkIfInitError(ctx, err) {
			return
		}
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("untaint", err))
		return
	}

	ctx.JSON(http.StatusOK, nil)
}

// VersionHandler calls Terraform version command
// @Summary     Shows the current Terraform version
// @Description Displays the current version of Terraform and all installed plugins
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     500 {object} TerraformError
// @Failure     500 {object} JsonMarshalError
// @Router      /version [get]
func (api Api) VersionHandler(ctx *gin.Context) {
	terraformVersion, providersVersion, err := api.Terraform.Version(ctx, true)
	if err != nil {
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("version", err))
		return
	}

	providers := make(map[string]string, len(providersVersion))
	for name, ver := range providersVersion {
		providers[name] = ver.String()
	}

	data, err := json.Marshal(TerraformVersionOutput{
		Version:   terraformVersion.String(),
		Providers: providers,
	})
	if err != nil {
		abortCall(ctx, http.StatusInternalServerError, JsonMarshalError{err})
		return
	}

	ctx.JSON(http.StatusOK, JSONResult{Data: data})
}

// WorkspaceShowHandler calls Terraform workspace show command
// @Summary     Shows the name of the current workspace
// @Description Outputs the current Terraform workspace
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     500 {object} TerraformError
// @Failure     500 {object} JsonMarshalError
// @Router      /workspace/show [get]
func (api Api) WorkspaceShowHandler(ctx *gin.Context) {
	currentWorkspace, err := api.Terraform.WorkspaceShow(ctx)
	if err != nil {
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("workspace show", err))
		return
	}

	out := TerraformWorkspaceShowOutput{Current: currentWorkspace}
	data, err := json.Marshal(out)
	if err != nil {
		abortCall(ctx, http.StatusInternalServerError, JsonMarshalError{err})
		return
	}

	ctx.JSON(http.StatusOK, JSONResult{Data: data})
}

// WorkspaceListHandler calls Terraform workspace list command
// @Summary     Lists Terraform workspaces
// @Description Lists all existing Terraform workspaces
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     400 {object} QueryError
// @Failure     500 {object} TerraformError
// @Failure     500 {object} NeedsInitError
// @Failure     500 {object} JsonMarshalError
// @Router      /workspace/list [get]
func (api Api) WorkspaceListHandler(ctx *gin.Context) {
	workspaceList, currentWorkspace, err := api.Terraform.WorkspaceList(ctx)
	if err != nil {
		if checkIfInitError(ctx, err) {
			return
		}
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("workspace list", err))
		return
	}

	out := TerraformWorkspaceListOutput{
		Current: currentWorkspace,
		List:    workspaceList,
	}
	data, err := json.Marshal(out)
	if err != nil {
		abortCall(ctx, http.StatusInternalServerError, JsonMarshalError{err})
		return
	}

	ctx.JSON(http.StatusOK, JSONResult{Data: data})
}

// WorkspaceSelectHandler calls Terraform workspace select command
// @Summary     Select a workspace
// @Description Chooses a different Terraform workspace to use for further operations
// @Param       name query string true "A name of existing Terraform workspace"
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     400 {object} QueryError
// @Failure     500 {object} TerraformError
// @Failure     500 {object} NeedsInitError
// @Router      /workspace/select [post]
func (api Api) WorkspaceSelectHandler(ctx *gin.Context) {
	var queryParams WorkspaceSelectQueryParams
	err := ctx.ShouldBindQuery(&queryParams)
	if err != nil {
		if checkIfInitError(ctx, err) {
			return
		}
		abortCall(ctx, http.StatusBadRequest, QueryError{err})
		return
	}

	err = api.Terraform.WorkspaceSelect(ctx, queryParams.Name)
	if err != nil {
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("workspace select", err))
		return
	}

	ctx.JSON(http.StatusOK, nil)
}

// WorkspaceNewHandler calls Terraform workspace new command
// @Summary     Creates a new workspace
// @Description Creates a new Terraform workspace with the given name
// @Param       name query string true "A name of (unexisting) Terraform workspace to be created"
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     400 {object} QueryError
// @Failure     500 {object} TerraformError
// @Failure     500 {object} NeedsInitError
// @Router      /workspace/new [post]
func (api Api) WorkspaceNewHandler(ctx *gin.Context) {
	var queryParams WorkspaceNewQueryParams
	err := ctx.ShouldBindQuery(&queryParams)
	if err != nil {
		if checkIfInitError(ctx, err) {
			return
		}
		abortCall(ctx, http.StatusBadRequest, QueryError{err})
		return
	}

	err = api.Terraform.WorkspaceNew(ctx, queryParams.Name)
	if err != nil {
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("workspace new", err))
		return
	}

	ctx.JSON(http.StatusOK, nil)
}

// WorkspaceDeleteHandler calls Terraform workspace delete command
// @Summary     Deletes a workspace
// @Description Deletes an existing Terraform workspace
// @Param       name query string true "A name of existing Terraform workspace to be deleted"
// @Produce     json
// @Success     200 {object} JSONResult
// @Failure     400 {object} QueryError
// @Failure     500 {object} TerraformError
// @Failure     500 {object} NeedsInitError
// @Router      /workspace/delete [delete]
func (api Api) WorkspaceDeleteHandler(ctx *gin.Context) {
	var queryParams WorkspaceDeleteQueryParams
	err := ctx.ShouldBindQuery(&queryParams)
	if err != nil {
		if checkIfInitError(ctx, err) {
			return
		}
		abortCall(ctx, http.StatusBadRequest, QueryError{err})
		return
	}

	err = api.Terraform.WorkspaceDelete(ctx, queryParams.Name)
	if err != nil {
		abortCall(ctx, http.StatusInternalServerError, newTerraformError("workspace delete", err))
		return
	}

	ctx.JSON(http.StatusOK, nil)
}
