provider "aws" {
  region = "${var.region}"
}

data "local_file" "ansible-ssm-document-content" {
  filename = "${path.module}/ansible_ssm_document.yml"
}

resource "aws_ssm_document" "ansible-ssm-document" {
  name            = "ec2-iam-users-${var.project-name}"
  document_type   = "Command"
  document_format = "YAML"
  content         = "${data.local_file.ansible-ssm-document-content.content}"

  tags {
    Name        = "ansible-ssm-document-${var.project-name}"
    Category    = "${var.category}"
    Project     = "${var.project-name}"
    Description = "Run the ec2-iam-users playbook to update the users for the instances in the project ${var.project-name}"
    Role        = "${var.role}"
  }
}

resource "null_resource" "cluster" {
  provisioner "local-exec" {
    inline = [
      "mkdir -p build/",
      "${jsonencode(path.module)}/pack-ansible.sh -o build/pack-ansible.zip",
    ]
  }
}

resource "aws_s3_bucket" "ansible-ssm-document-bucket" {
  bucket_prefix = "ec2-iam-users-${var.project-name}"
  acl           = "private"

  tags {
    Name        = "ansible-ssm-document-bucket-${var.project-name}"
    Category    = "${var.category}"
    Project     = "${var.project-name}"
    Description = "Hosts the ec2-iam-users playbook to update the users for the instances in the project ${var.project-name}"
    Role        = "${var.role}"
  }
}

resource "aws_s3_bucket_object" "ansible-ssm-document-object" {}
