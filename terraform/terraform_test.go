package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	// "github.com/stretchr/testify/assert"
)

func TestTerraform(t *testing.T) {
	terraformOptions := &terraform.Options{
		TerraformDir: "./resources",
		NoColor:      true,
		Vars: map[string]interface{}{
			"region":       "us-east-2",
			"project-name": "ec2-iam-users-test",
		},
	}

	defer terraform.Destroy(t, terraformOptions)

	terraform.InitAndApply(t, terraformOptions)
}
