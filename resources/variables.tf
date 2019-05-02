variable "region" {
  default = "us-east-2"
}

variable "project-name" {
  description = "Name of the project, will be used an identified suffix"
  type        = "string"
}

variable "category" {
  default     = "security"
  description = "Value to set to 'Category' tag"
  type        = "string"
}

variable "role" {
  default     = "network"
  description = "Value to set to 'Role' tag"
  type        = "string"
}
