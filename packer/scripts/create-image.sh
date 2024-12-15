#!/bin/bash
# Script taken from: Ivan Velichko's Docker-to-Linux GitHub Repository
# Source File: https://github.com/iximiuz/docker-to-linux/blob/master/create_image.sh
# License: UNLICENSED

set -e

echo_blue() {
    local font_blue="\033[94m"
    local font_bold="\033[1m"
    local font_end="\033[0m"

    echo -e "\n${font_blue}${font_bold}${1}${font_end}"
}

echo_blue "[Install APT dependencies]"
DEBIAN_FRONTEND=noninteractive apt-get install --reinstall coreutils # Some /bin tools might not exist
DEBIAN_FRONTEND=noninteractive apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
  apt-utils\
  debconf\
  dosfstools\
  efibootmgr\
  extlinux\
  fdisk\
  parted\
  qemu-utils

echo_blue "[Create disk image]"
dd if=/dev/zero of=/os/${DISTR}.img bs=$(expr 1024 \* 1024 \* 1024) count=32

echo_blue "[Make partition]"
sfdisk /os/${DISTR}.img < /os/config/partition.txt

# https://gist.github.com/gnthibault/11fb1d1598f5f6e5324cd6c0aca8a2a9
echo_blue "\n[Format partition with ext4]"
losetup -D
LOOPDEVICE=$(losetup -f)
echo -e "\n[Using ${LOOPDEVICE} loop device]"
# The offset must be after the EFI partition of 100MB that starts at 1Mib (4096 sectors)
LOG_SECTOR_SIZE=$(fdisk -l /os/${DISTR}.img | awk '$1 == "Sector" {print $4}')
PHY_SECTOR_SIZE=$(fdisk -l /os/${DISTR}.img | awk '$1 == "Sector" {print $7}')
UNIT_SIZE=$(fdisk -l /os/${DISTR}.img | awk '$1 == "Units:" {print $8}')
EXT_OFFSET=$(fdisk -l /os/${DISTR}.img | awk '$1 == "'"/os/${DISTR}.img2"'" {print $2}')
EXT_SIZE=$(fdisk -l /os/${DISTR}.img | awk '$1 == "'"/os/${DISTR}.img2"'" {print $4}')
losetup -o  $(expr $EXT_OFFSET \* $UNIT_SIZE) --sizelimit=$(expr $EXT_SIZE \* $UNIT_SIZE) ${LOOPDEVICE} /os/${DISTR}.img #--sector-size=4096
mkfs.ext4 ${LOOPDEVICE}

echo_blue "[Copy ${DISTR} directory structure to partition]"
mkdir -p /os/mnt
mount -t auto ${LOOPDEVICE} /os/mnt/
# Also make sure that proper module will be loaded at boot time
cp -p /os/config/${DISTR}/vfat.conf /os/${DISTR}.dir/etc/modules-load.d/vfat.conf
cp -p /os/config/${DISTR}/fstab /os/${DISTR}.dir/etc/fstab
cp -p /os/config/${DISTR}/hosts /os/${DISTR}.dir/etc/hosts
cp -p /os/config/${DISTR}/01-netcfg.yaml /os/${DISTR}.dir/etc/netplan/01-netcfg.yaml
#cp /os/config/${DISTR}/resolved.conf /os/${DISTR}.dir/etc/systemd/resolved.conf
rm -f /os/${DISTR}.dir/etc/resolv.conf
ln -s /run/systemd/resolve/resolv.conf /os/${DISTR}.dir/etc/resolv.conf
echo "PermitRootLogin yes" >> /os/${DISTR}.dir/etc/ssh/sshd_config
# Make sure /efi exist to mount ESP later on, see also https://wiki.archlinux.org/title/EFI_system_partition#Using_systemd
#mkdir -p /os/${DISTR}.dir/efi
# -p: --preserve=mode,ownership,timestamps, -d: --no-dereference --preserve=links
cp -pdr /os/${DISTR}.dir/. /os/mnt/



echo_blue "[Unmounting linux partition]"
umount /os/mnt
losetup -d ${LOOPDEVICE}

echo_blue "[Setup extlinux]" # https://wiki.archlinux.org/title/Syslinux
EFILOOPDEVICE=$(losetup -f)
# The offset must be 1Mib bytes (4096 sectors) - https://man7.org/linux/man-pages/man8/losetup.8.html
EFI_OFFSET=$(fdisk -l /os/${DISTR}.img | awk '$1 == "'"/os/${DISTR}.img1"'" {print $2}')
EFI_SIZE=$(fdisk -l /os/${DISTR}.img | awk '$1 == "'"/os/${DISTR}.img1"'" {print $4}')
losetup -o $(expr $EFI_OFFSET \* $UNIT_SIZE) --sizelimit=$(expr $EFI_SIZE \* $UNIT_SIZE) ${EFILOOPDEVICE} /os/${DISTR}.img
echo_blue "[Formatting the EFI partition as FAT32]"
# Format the EFI partition as FAT32
mkfs.fat -F32 ${EFILOOPDEVICE}
mkdir -p /os/efi
mount -t auto ${EFILOOPDEVICE} /os/efi/
# For Syslinux, the kernel and initramfs files need to be in the EFI system partition (aka ESP), as Syslinux does not
# (currently) have the ability to access files outside its own partition (i.e. outside ESP in this case).
# For this reason, it is recommended to mount ESP at /boot
# The configuration syntax of syslinux.cfg for UEFI is same as that of BIOS


# https://superuser.com/questions/1825395/whats-the-easiest-path-to-make-my-extlinux-booted-ubuntu-bootable-via-uefi
# The Syslinux configuration file, syslinux.cfg, should be created in the same directory where you installed Syslinux.
# In our case, /boot/syslinux/ for BIOS systems and esp/EFI/syslinux/ for UEFI systems.
# extlinux --install /os/mnt/boot/
# /os/config/${DISTR}/syslinux.cfg /os/mnt/boot/syslinux.cfg
#mkdir -p /os/efi/EFI/syslinux
mkdir -p /os/efi/EFI/boot
cp -rL /os/${DISTR}.dir/usr/lib/syslinux/modules/efi64/* /os/efi/EFI/boot/
cp -rL /os/${DISTR}.dir/usr/lib/SYSLINUX.EFI/efi64/syslinux.efi /os/efi/EFI/boot/bootx64.efi
cp /os/config/${DISTR}/syslinux.cfg /os/efi/EFI/boot/syslinux.cfg
cp -rL /os/${DISTR}.dir/boot/vmlinuz /os/efi/EFI/boot/vmlinuz
cp -rL /os/${DISTR}.dir/boot/initrd.img /os/efi/EFI/boot/initrd.img

#cp -r /os/${DISTR}.dir/usr/lib/SYSLINUX.EFI/efi64/* /os/efi/EFI/syslinux
#cp /os/config/${DISTR}/syslinux.cfg /os/efi/EFI/syslinux/syslinux.cfg

echo_blue "[Unmounting EFI partition]"
umount /os/efi
losetup -d ${EFILOOPDEVICE}

#echo_blue "[Write syslinux MBR]"
#dd if=/usr/lib/syslinux/mbr/mbr.bin of=/os/${DISTR}.img bs=440 count=1 conv=notrunc
# efibootmgr --create --disk /dev/sdX --part Y --loader /EFI/syslinux/syslinux.efi --label "Syslinux" --unicode
# where /dev/sdXY is the EFI system partition containing the boot loader.
# https://discuss.hashicorp.com/t/cant-get-uefi-boot-order-to-work-properly-bdsdxe-failed-to-load-boot0001-uefi-vbox-harddisk-arch-linux-virtualbox-iso/55136
# https://wiki.gentoo.org/wiki/EFI_stub#Installation

#echo_blue "[Write EFI boot config]"
#efibootmgr --create --disk /os/${DISTR}.img --part 1 --loader /EFI/syslinux/syslinux.efi --label "Syslinux" --unicode
#efibootmgr --create --disk /os/${DISTR}.img --part 1 --loader /EFI/boot/bootx64.efi --test /os/${DISTR}.nvram --label "Syslinux" --unicode

# Qemu first time workflow
# Pres esc when booting to access bios
# select EFI shell option and enter
# help bcfg -b
# bcfg boot dump -b
# Search for  UEFI QEMU HARDDISK QM00001 entry option number (here 5)
# bcfg boot mv 5 0
# If corresponding entry does not exist or does not work with you customized EFI bootloader you might create one
# bcfg boot add 1 FS0:\EFI\boot\bootx64.efi

# For some reason is seems that we also need to fix the ext4 partition...
#echo_blue "[Repare ext4 system partition1]"
#ALLLOOPDEVICE=$(losetup -f)
#losetup -${ALLLOOPDEVICE} /os/${DISTR}.img
#partprobe $ALLLOOPDEVICE
# Get the loop device for the ext4 partition
#EXT_DEVICE="${ALLLOOPDEVICE}p2"
#e2fsck -fn $EXT_DEVICE
#resize2fs $EXT_DEVICE
#losetup -d ${ALLLOOPDEVICE}
# https://mricher.fr/post/boot-from-an-efi-shell/
#/usr/bin/arch-chroot ${ROOT_DIR} grub-install --target=x86_64-efi --efi-directory=${ESP_DIR} --bootloader-id=GRUB --removeable &>/dev/null
#grub-install --target=x86_64-efi --efi-directory=/mnt/efi --bootloader-id=GRUB --removable
#cat > /mnt/efi/EFI/GRUB/grub.cfg <<EOF
#set default=0
#set timeout=5
#menuentry "Linux" {
#    linux /vmlinuz root=/dev/sda2
#    initrd /initrd.img
#}
#EOF

echo_blue "[Output sha256 to file]"
cd /os
sha256sum ./${DISTR}.img > /os/ubuntu.sha256
cd -

#echo_blue "[Convert to qcow2]"
#qemu-img convert -c /os/${DISTR}.img -O qcow2 /os/${DISTR}.qcow2
