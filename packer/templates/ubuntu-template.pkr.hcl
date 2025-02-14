#     PockerISO: Use Packer + Docker to make bootable images
#     Copyright (C) 2022  Shantanoo 'Shan' Desai <sdes.softdev@gmail.com>

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.


packer {
  required_plugins {
    docker = {
      version = ">= 1.0.1"
      source = "github.com/hashicorp/docker"
    }
    qemu = {
      version = "~> 1"
      source  = "github.com/hashicorp/qemu"
    }
  }
}

variable distro {
    type = string
}

variable distro_version {
    type = string
}

variable distro_platform {
    type = string
    default = "linux/amd64"
}

variable distro_kernel {
    type = string
}

locals {
    distro_docker_image = "${var.distro}:${var.distro_version}"
}

# This Source will only be used to create a Filesystem from the Docker Container
source "docker" "filesystem-container" {
    image = "${local.distro_docker_image}"
    pull = true # save bandwidth and avoid multiple pulls to same image
    platform = "${var.distro_platform}"
    export_path = "./${var.distro}.tar"
}

# This source will be use to create a Bootable Disk Image from the Generated Filesystem
source "docker" "partition-container" {
    image = "${local.distro_docker_image}"
    pull = false
    platform = "${var.distro_platform}"
    discard = true
    cap_add = [ "SYS_ADMIN" ]
    privileged = true
    volumes = {
        "${path.cwd}": "/os"
    }
}

build {
    # Install the Respective Kernel and SystemD
    name = "gen-fs-tarball"
    sources = [ "source.docker.filesystem-container" ]
    provisioner "shell" {
        inline = [
            "apt-get install --reinstall coreutils", # Some /bin tools might not exist
            "apt-get update",
            "DEBIAN_FRONTEND=noninteractive apt-get install -y ${var.distro_kernel}",
            "DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends systemd-sysv",
            "echo \"root:root\" | chpasswd"
        ]
    }
}

build {
    # generate a bootable disk image
    name = "gen-boot-img"
    sources = [ "source.docker.partition-container" ]
    provisioner "shell" {
        environment_vars = [
            "DISTR=${var.distro}"
        ]
        scripts = [
            "./scripts/create-image.sh"
        ]
    }
}

# https://developer.hashicorp.com/packer/integrations/hashicorp/qemu/latest/components/builder/qemu
source "qemu" "qemu-boot-img" {
  disk_image        = true
  iso_url           = "./ubuntu.img"
  #iso_checksum     = "file:./sha256sum.txt"
  iso_checksum      = "none"
  output_directory  = "./ubuntu.output"
  communicator      = "ssh" # https://developer.hashicorp.com/packer/integrations/hashicorp/qemu/latest/components/builder/qemu#optional-ssh-fields:
  ssh_username      = "root"
  ssh_password      = "root"
  ssh_timeout       = "20m"
  shutdown_command  = "echo 'packer' | sudo -S shutdown -P now"
  disk_size         = "5G"
  format            = "raw"
  accelerator       = "kvm"
  http_directory    = "../"
  vm_name           = "customized_ubuntu"
  net_device        = "virtio-net"
  disk_interface    = "virtio"
  boot_wait         = "10s"
  boot_command      = []
}

build {
  sources = ["qemu.qemu-boot-img"]

  provisioner "shell" {
    environment_vars = [
      "HOME_DIR=/opt/remote_observatory"
    ]
    execute_command = "echo 'vagrant' | {{ .Vars }} sudo -S -E sh -eux '{{ .Path }}'"
    scripts = ["scripts/ubuntu_install.sh"]
    expect_disconnect = true
  }
  post-processors {
    post-processor "compress" {
      compression_level   = 6
      format              = ".gz"
      keep_input_artifact = true
      only                = ["qemu"]
      output              = "./customized_ubuntu.img.gz"
    }
  }
}