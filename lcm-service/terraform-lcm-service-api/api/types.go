package api

import (
	"encoding/json"

	"github.com/gin-gonic/gin"
	"github.com/hashicorp/terraform-exec/tfexec"
	tfjson "github.com/hashicorp/terraform-json"
)

// Api holds the main API object
type Api struct {
	Configuration Configuration
	Terraform     *tfexec.Terraform
	Router        *gin.Engine
}

// Configuration holds API configuration settings
type Configuration struct {
	Version          string
	TerraformVersion string
	WorkingDirectory string
	DebugMode        bool
	Port             string
	SwaggerUrl       string
	TrustedProxy     string
}

// JSONResult represents API JSON response
type JSONResult struct {
	Message string          `json:"message"`
	Data    json.RawMessage `json:"data"`
}

// PlanQueryParams represents query params for /plan handle
type PlanQueryParams struct {
	Vars     []string `form:"vars"`
	VarFiles []string `form:"var_files"`
}

// ApplyQueryParams represents query params for /apply handle
type ApplyQueryParams struct {
	RefreshOnly bool     `form:"refresh_only"`
	Replace     string   `form:"replace"`
	Vars        []string `form:"vars"`
	VarFiles    []string `form:"var_files"`
	Parallelism int      `form:"parallelism"`
}

// DestroyQueryParams represents query params for /destroy handle
type DestroyQueryParams struct {
	Vars        []string `form:"vars"`
	VarFiles    []string `form:"var_files"`
	Parallelism int      `form:"parallelism"`
}

// ForceUnlockQueryParams represents query params for /force-unlock handle
type ForceUnlockQueryParams struct {
	LockId string `form:"lock_id"`
}

// ImportQueryParams represents query params for /import handle
type ImportQueryParams struct {
	Address string `form:"address"`
	Id      string `form:"id"`
}

// StateRmQueryParams represents query params for /state/rm handle
type StateRmQueryParams struct {
	Address string `form:"address"`
}

// StateMvQueryParams represents query params for /state/mv handle
type StateMvQueryParams struct {
	Source      string `form:"source"`
	Destination string `form:"destination"`
}

// UntaintQueryParams represents query params for /untaint handle
type UntaintQueryParams struct {
	Address string `form:"address"`
}

// WorkspaceSelectQueryParams represents query params for /workspace/select handle
type WorkspaceSelectQueryParams struct {
	Name string `form:"name"`
}

// WorkspaceNewQueryParams represents query params for /workspace/new handle
type WorkspaceNewQueryParams struct {
	Name string `form:"name"`
}

// WorkspaceDeleteQueryParams represents query params for /workspace/delete handle
type WorkspaceDeleteQueryParams struct {
	Name string `form:"name"`
}

// TerraformValidateOutput represents output for /validate handle
type TerraformValidateOutput struct {
	tfjson.ValidateOutput
}

// TerraformPlanOutput represents output for /plan handle
type TerraformPlanOutput struct {
	Changed bool `json:"formatted,omitempty"`
}

// TerraformFormatOutput represents output for /fmt handle
type TerraformFormatOutput struct {
	Formatted    bool     `json:"formatted,omitempty"`
	ChangedFiles []string `json:"changed_files,omitempty"`
}

// TerraformGraphOutput represents output for /graph handle
type TerraformGraphOutput struct {
	Output string `json:"formatted,omitempty"`
}

// TerraformOutputOutput represents output for /output handle
type TerraformOutputOutput struct {
	Output map[string]tfexec.OutputMeta `json:"output,omitempty"`
}

// TerraformProvidersSchemaOutput represents output for /providers/schema handle
type TerraformProvidersSchemaOutput struct {
	tfjson.ProviderSchemas
}

// TerraformShowOutput represents output for /show handle
type TerraformShowOutput struct {
	tfjson.State
}

// TerraformVersionOutput represents output for /version handle
type TerraformVersionOutput struct {
	Version   string            `json:"version,omitempty"`
	Providers map[string]string `json:"providers,omitempty"`
}

// TerraformWorkspaceShowOutput represents output for /workspace/show handle
type TerraformWorkspaceShowOutput struct {
	Current string `json:"formatted,omitempty"`
}

// TerraformWorkspaceListOutput represents output for /workspace/list handle
type TerraformWorkspaceListOutput struct {
	Current string   `json:"current,omitempty"`
	List    []string `json:"list,omitempty"`
}
