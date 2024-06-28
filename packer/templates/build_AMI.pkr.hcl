
variable "aws_access_key" {
  type    = string
  default = ""
}

variable "aws_secret_key" {
  type    = string
  default = ""
}

variable "aws_profile_name" {
  type    = string
  default = "igvf-dev"
}

variable "aws_region" {
  type = string
}

variable "ssh_username" {
  type = string
  default = "ubuntu"
}

variable "name_tag" {
  type  = string
  default = "catalog_web_AMI"
}

variable "installation_scripts" {
  type = list(string)
}

variable "ami_type" {
  type = string
  description = "This will be written in custom_data in the manifest.json"
}

variable "source_ami_name" {
  type = string
  description = "Source AMI used to search for the base AMI for the build"
}

locals { timestamp = regex_replace(timestamp(), "[- TZ:]", "") }

source "amazon-ebs" "builder" {
  profile       = "${var.aws_profile_name}"
  ami_name      = "packer-ami-build ${local.timestamp}"
  instance_type = "m3.medium"
  region        = "${var.aws_region}"
  ssh_username  = "${var.ssh_username}"
  tags = {
    Name = "${var.name_tag}"
  }
  source_ami_filter {
    filters = {
      virtualization-type = "hvm"
        name = "${var.source_ami_name}"
        root-device-type = "ebs"
    }
    owners = ["099720109477"]
    most_recent = true
  }
}

# a build block invokes sources and runs provisioning steps on them. The
# documentation for build blocks can be found here:
# https://www.packer.io/docs/from-1.5/blocks/build
build {
  sources = ["source.amazon-ebs.builder"]

  provisioner "file" {
    source = "../files/amazon-cloudwatch-agent.json"
    destination = "/tmp/amazon-cloudwatch-agent.json"
  }

  provisioner "shell" {
    pause_before = "60s"
    scripts = "${var.installation_scripts}"
    max_retries = 5
  }
  post-processor "manifest" {
    output = "manifest.json"
    custom_data = {
      ami_type = "${var.ami_type}"
    }
  }
}
