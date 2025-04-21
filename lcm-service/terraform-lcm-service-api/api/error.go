package api

import (
	"errors"
	"fmt"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/hashicorp/terraform-exec/tfexec"
	log "github.com/sirupsen/logrus"
)

// abortCall aborts from the API
func abortCall(ctx *gin.Context, statusCode int, err error) {
	log.Error(err)
	ctx.AbortWithStatusJSON(statusCode, JSONResult{Message: err.Error(), Data: nil})
	errAbort := ctx.AbortWithError(statusCode, err)
	if errAbort != nil {
		return
	}
}

// newTerraformError creates a new TerraformError
func newTerraformError(command string, err error) TerraformError {
	return TerraformError{
		command: command,
		err:     err,
	}
}

// TerraformError is returned whenever something regarding Terraform fails
// if there is a more specific error regarding Terraform, the other is returned instead
type TerraformError struct {
	command string
	err     error
}

// Error prints out TerraformError as string
func (e TerraformError) Error() string {
	return fmt.Sprintf("running Terraform command \"%v\" failed: %s", e.command, e.err)
}

// NeedsInitError is returned when the folder containing the Terraform files is not initialized yet
type NeedsInitError struct {
	err error
}

// Error prints out NeedsInitError as string
func (e NeedsInitError) Error() string {
	return fmt.Sprintf("Terraform folder is not initialized: %s", e.err)
}

// QueryError is returned when the provided queries don't match the target struct
type QueryError struct {
	err error
}

// Error prints out QueryError as string
func (e QueryError) Error() string {
	return fmt.Sprintf("validating queries: %s", e.err)
}

// JsonMarshalError is returned when building JSON object fails
type JsonMarshalError struct {
	err error
}

// Error prints out JsonMarshalError as string
func (e JsonMarshalError) Error() string {
	return fmt.Sprintf("building (marshal) JSON: %s", e.err)
}

// checkIfInitError will check if the error is of type tfexec.NoInitEr and if so will abort the context and return true
func checkIfInitError(ctx *gin.Context, err error) bool {
	var noInitErr *tfexec.ErrNoInit
	if errors.Is(err, noInitErr) {
		abortCall(ctx, http.StatusInternalServerError, NeedsInitError{err: err})
		return true
	}
	return false
}
