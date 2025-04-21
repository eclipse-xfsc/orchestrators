package api

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"sync"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

var c = &engineCache{
	cache: make(map[string]*gin.Engine),
}

func CommonTestCase[K any](t *testing.T, httpRequest *http.Request, terraformFolder string) (int, K) {
	defer cleanup(t, terraformFolder)

	router, err := c.getRouterForFolder(terraformFolder)
	if err != nil {
		t.Fatal(err)
	}

	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, httpRequest)

	out := new(K)
	unmarshal(t, recorder.Body.Bytes(), out)

	return recorder.Code, *out
}

func unmarshal[K any](t *testing.T, msg json.RawMessage, into *K) {
	err := json.Unmarshal(msg, into)
	if err != nil {
		t.Errorf("Cannot unmarshal JSON: %s", err)
	}
}

type engineCache struct {
	cache map[string]*gin.Engine
	mut   sync.Mutex
}

// getRouterForFolder creates a gin engine for each
func (c *engineCache) getRouterForFolder(folder string) (*gin.Engine, error) {
	fmt.Printf("Access for folder: %s\n", folder)
	c.mut.Lock()
	gin.SetMode(gin.TestMode)
	router, ok := c.cache[folder]
	c.mut.Unlock()
	if !ok {
		fmt.Printf("folder %s entry not found, creating new engine\n", folder)
		apiConfig := SetupApiConfiguration()
		tf, err := SetupTerraform(context.Background(), apiConfig.TerraformVersion, folder)
		if err != nil {
			return nil, err
		}
		api := Api{Terraform: tf, Configuration: apiConfig}
		newRouter, err := SetupRouter(api)
		if err != nil {
			return nil, err
		}
		router = newRouter
		c.mut.Lock()
		c.cache[folder] = router
		c.mut.Unlock()
	}
	return router, nil
}

func TestInitRoute(t *testing.T) {
	type expected struct {
		statusCode int
	}
	testCases := []struct {
		name            string
		terraformFolder string
		expected        expected
	}{
		{
			name:            "hello-world",
			terraformFolder: "../tests/hello-world",
			expected: expected{
				statusCode: 200,
			},
		},
		{
			name:            "non-Terraform",
			terraformFolder: "../tests/non-terraform",
			expected: expected{
				statusCode: 200,
			},
		},
	}

	for _, tt := range testCases {
		t.Run(tt.name, func(t *testing.T) {
			tt := tt // see https://github.com/golang/go/wiki/CommonMistakes#using-goroutines-on-loop-iterator-variables
			t.Parallel()
			req, _ := http.NewRequest("POST", "/init", nil)
			statusCode, _ := CommonTestCase[struct{}](t, req, tt.terraformFolder)
			assert.Equal(t, tt.expected.statusCode, statusCode)
		})
	}
}

func TestValidateRoute(t *testing.T) {
	type expected struct {
		statusCode int
		// use 0 to indicate no errors and >0 to expect errors
		errors uint
		// to check if the files are valid tf syntax
		valid bool
	}
	testCases := []struct {
		name            string
		terraformFolder string
		expected        expected
		wantErr         bool
	}{
		{
			name:            "hello-world",
			terraformFolder: "../tests/hello-world",
			expected: expected{
				statusCode: 200,
				errors:     0,
			},
		},
		{
			name:            "non-Terraform",
			terraformFolder: "../tests/non-terraform",
			expected: expected{
				statusCode: 200,
			},
		},
		{
			name:            "invalid",
			terraformFolder: "../tests/invalid",
			expected: expected{
				statusCode: 200,
				valid:      false,
			},
		},
	}

	for _, tt := range testCases {
		t.Run(tt.name, func(t *testing.T) {
			tt := tt // see https://github.com/golang/go/wiki/CommonMistakes#using-goroutines-on-loop-iterator-variables
			t.Parallel()
			req, _ := http.NewRequest("POST", "/validate", nil)
			statusCode, got := CommonTestCase[TerraformValidateOutput](t, req, tt.terraformFolder)
			assert.Equal(t, tt.expected.statusCode, statusCode)
			if tt.expected.errors == 0 {
				assert.Equal(t, 0, got.ErrorCount)
			} else {
				assert.GreaterOrEqual(t, got.ErrorCount, tt.expected.errors)
			}
			assert.Equal(t, tt.expected.valid, got.Valid)
		})
	}
}

func TestPlanRoute(t *testing.T) {
	type expected struct {
		statusCode  int
		planChanged TerraformPlanOutput
	}
	testCases := []struct {
		name            string
		terraformFolder string
		expected        expected
	}{
		{
			name:            "hello-world",
			terraformFolder: "../tests/hello-world",
			expected: expected{
				statusCode:  200,
				planChanged: TerraformPlanOutput{Changed: false},
			},
		},
		{
			name:            "non-Terraform",
			terraformFolder: "../tests/non-terraform",
			expected: expected{
				statusCode: 500,
				planChanged: TerraformPlanOutput{Changed: false},
			},
		},
		{
			name:            "invalid",
			terraformFolder: "../tests/invalid",
			expected: expected{
				statusCode: 500,
				planChanged: TerraformPlanOutput{Changed: false},
			},
		},
	}

	for _, tt := range testCases {
		t.Run(tt.name, func(t *testing.T) {
			tt := tt // See https://github.com/golang/go/wiki/CommonMistakes#using-goroutines-on-loop-iterator-variables
			t.Parallel()
			req, _ := http.NewRequest("POST", "/plan", nil)
			statusCode, output := CommonTestCase[TerraformPlanOutput](t, req, tt.terraformFolder)

			assert.Equal(t, tt.expected.statusCode, statusCode)
			assert.Equal(t, tt.expected.planChanged, output)
		})
	}

}

func TestApplyRoute(t *testing.T) {
	type expected struct {
		statusCode int
	}
	testCases := []struct {
		name            string
		terraformFolder string
		expected        expected
	}{
		{
			name:            "hello-world",
			terraformFolder: "../tests/hello-world",
			expected: expected{
				statusCode: 200,
			},
		},
		{
			name:            "non-Terraform",
			terraformFolder: "../tests/non-terraform",
			expected: expected{
				statusCode: 500,
			},
		},
	}

	for _, tt := range testCases {
		t.Run(tt.name, func(t *testing.T) {
			tt := tt // See https://github.com/golang/go/wiki/CommonMistakes#using-goroutines-on-loop-iterator-variables
			t.Parallel()
			req, _ := http.NewRequest("POST", "/apply", nil)
			statusCode, _ := CommonTestCase[struct{}](t, req, tt.terraformFolder)

			assert.Equal(t, tt.expected.statusCode, statusCode)
		})
	}
}

func TestDestroyRoute(t *testing.T) {
	type expected struct {
		statusCode int
	}
	testCases := []struct {
		name            string
		terraformFolder string
		expected        expected
	}{
		{
			name:            "hello-world",
			terraformFolder: "../tests/hello-world",
			expected: expected{
				statusCode: 200,
			},
		},
		{
			name:            "non-Terraform",
			terraformFolder: "../tests/non-terraform",
			expected: expected{
				statusCode: 200,
			},
		},
	}

	for _, tt := range testCases {
		t.Run(tt.name, func(t *testing.T) {
			tt := tt // See https://github.com/golang/go/wiki/CommonMistakes#using-goroutines-on-loop-iterator-variables
			t.Parallel()
			req, _ := http.NewRequest("POST", "/destroy", nil)
			statusCode, _ := CommonTestCase[struct{}](t, req, tt.terraformFolder)

			assert.Equal(t, tt.expected.statusCode, statusCode)
		})
	}
}

func cleanup(t *testing.T, folder string) {
	err := os.RemoveAll(filepath.Join(folder, ".Terraform"))
	if err != nil {
		t.Logf("removing .Terraform: %v", err)
	}
	stateFiles, err := filepath.Glob("Terraform.tfstate*")
	if err != nil {
		t.Logf("finding Terraform.tfstate files: %v", err)
	}
	// prevent nil pointer panic
	if stateFiles == nil {
		stateFiles = make([]string, 0)
	}
	for _, statefile := range stateFiles {
		err := os.RemoveAll(statefile)
		if err != nil {
			t.Logf("removing Terraform.tfstate files: %v", err)
		}
	}
}
