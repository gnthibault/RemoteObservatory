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

variable base_docker_image {
  type = string
  default = "europe-west1-docker.pkg.dev/remote-observatory-dev-jcy/remote-observatory-main-repo/remote_observatory:latest"
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
    base_docker_image = var.base_docker_image #"${var.distro}:${var.distro_version}"
}

# This Source will only be used to create a Filesystem from the Docker Container
# https://developer.hashicorp.com/packer/integrations/hashicorp/docker/latest/components/builder/docker#configuration-reference
source "docker" "filesystem-container" {
    image = "${local.base_docker_image}"
    pull = true # save bandwidth and avoid multiple pulls to same image
    platform = "${var.distro_platform}"
    export_path = "./${var.distro}.tar"
    exec_user = "root"
#     changes = [
#       "USER www-data",
#       "WORKDIR /var/www",
#       "ENV HOSTNAME www.example.com",
#       "VOLUME /test1 /test2",
#       "EXPOSE 80 443",
#       "LABEL version=1.0",
#       "ONBUILD RUN date",
#       "CMD [\"nginx\", \"-g\", \"daemon off;\"]",
#       "ENTRYPOINT /var/www/start.sh"
#     ]
}

# This source will be use to create a Bootable Disk Image from the Generated Filesystem
source "docker" "partition-container" {
    image = "${var.distro}:${var.distro_version}"
    pull = true
    platform = "${var.distro_platform}"
    exec_user = "root"
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
            "DEBIAN_FRONTEND=noninteractive apt-get install -y initramfs-tools ${var.distro_kernel}",
            "DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends systemd-sysv",
            "echo \"root:root\" | chpasswd"
        ]
    }
    provisioner "shell" {
        inline = [ <<EOF
            DEBIAN_FRONTEND=noninteractive apt-get install -y\
             dnsutils\
             efibootmgr\
             inetutils-ping\
             net-tools\
             netplan.io\
             network-manager\
             openssh-server\
             ovmf\
             resolvconf\
             syslinux-common\
             syslinux-efi\
             tcptraceroute\
             vim
         EOF
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
  #accelerator        = "kvm"
  boot_command       = []
  boot_wait          = "45s" # Time to wait before typing boot command
  cdrom_interface    = "virtio"
  communicator       = "ssh" # https://developer.hashicorp.com/packer/integrations/hashicorp/qemu/latest/components/builder/qemu#optional-ssh-fields:
  disk_compression   = true
  disk_interface     = "virtio"
  disk_image         = true
  disk_size          = "10G"
  efi_boot           = true # https://developer.hashicorp.com/packer/integrations/hashicorp/qemu/latest/components/builder/qemu#efi-boot-configuration
  efi_drop_efivars   = true
  efi_firmware_code  = "./config/OVMF_CODE.fd"
  efi_firmware_vars  = "./config/OVMF_VARS.fd"
  format             = "raw"
  headless           = false
  http_directory     = "../"
  iso_checksum       = "none" #"file:./ubuntu.sha256"
  iso_url            = "./ubuntu.img"
  net_device         = "virtio-net"
  output_directory   = "./ubuntu.output" # "artifacts/qemu/${var.name}${var.version}"
  qemuargs = [
    ["-m", "4096"],  # "${var.ram}M"
    ["-smp", "4"],   # "${var.cpu}"
    ["-drive", "if=pflash,format=raw,readonly=on,file=./config/OVMF_CODE.fd"],
    ["-drive", "if=pflash,format=raw,readonly=on,file=./config/OVMF_VARS.fd"],
    ["-drive", "file=ubuntu.output/customized_ubuntu,index=0,media=disk,format=raw"],
    ["-netdev", "user,id=net0"],
    ["-net", "user,hostfwd=tcp::{{ .SSHHostPort }}-:22"],
    ["-net", "nic"],
    ["-device", "virtio-net,netdev=net0"]
  ]
  shutdown_command   = "shutdown -P now" #"echo '${var.ssh_password}' | sudo -S shutdown -P now"
  skip_resize_disk   = true
  ssh_password       = "root" #var.ssh_password
  ssh_port           = 22
  ssh_username       = "root" #var.ssh_username
  ssh_timeout        = "10m"
  use_default_display = true
  use_pflash         = true
  vm_name            = "customized_ubuntu"
}


build {
  # Customize bootable disk image further with applications
  name = "customize-boot-img"
  sources = ["qemu.qemu-boot-img"]

  provisioner "shell" {
    environment_vars = [
      "HOME_DIR=/opt/remote_observatory"
    ]
#     execute_command = "echo 'vagrant' | {{ .Vars }} sudo -S -E sh -eux '{{ .Path }}'"
#    execute_command = "{{ .Vars }} sudo -E bash '{{ .Path }}'"
    execute_command = "{{ .Vars }} bash '{{ .Path }}'"
    scripts = ["../infrastructure/run_install_script.sh"] #["scripts/ubuntu_install.sh"]
    expect_disconnect = true
  }
  post-processors {
#     post-processor "shell-local" {
#       environment_vars = ["IMAGE_NAME=${var.name}", "IMAGE_VERSION=${var.version}", "IMAGE_FORMAT=${var.format}"]
#       script           = "scripts/prepare-image.sh"
#     }
    post-processor "compress" {
      format              = ".gz"
      compression_level   = 6
      keep_input_artifact = false
      output              = "./customized_ubuntu.img.gz"
    }
  }
}
