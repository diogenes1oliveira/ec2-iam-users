provider "aws" {
  region = "${var.region}"
}

data "local_file" "foo" {
  filename = "${path.module}/resources/ansible_ssm_document.yml"
}

resource "aws_ssm_document" "iam-syncer" {
  name          = "iam-syncer-${var.project-name}"
  document_type = "YAML"
}
