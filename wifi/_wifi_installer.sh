#!/bin/bash

# --- Helper functions for sanity. -------------------------------------

# fbutil shell script library.

# This provides common features to all shell scripts that uses fbutil.

# fbutil is a very simple utility that allows the users to print to the
# framebuffer on HRCB.

# We start at 10 pixels from the top for readability.
FB_Y=10
FBUTIL=fbutil

FBUTIL=/stinger/app/bin/fbutil
usb_dir=/media/usb0
fb_println()
{
    # Print a line on framebuffer.

    # We manually have to advance lines correctly in pixels because
    # fbutil is a oneshot utility.  Linux framebuffer driver manages the
    # buffer.  We do not have to worry about fadeout.

    # Notice that we don't use '-x'. Default is 10, and that works well.
    # 18 pixels = 16 + 2 = Font_Height + Line_Spacing.

    $FBUTIL -y $FB_Y "$*"
    FB_Y=$((FB_Y + 18))
}

fb_clear()
{
    FB_Y=10
    $FBUTIL -c
}


##### Main script. #####################################################

# trap "error 1" EXIT

# Be verbose for debugging and logging.
# set -x

# Clear the screen.
fb_clear

# fb_println "Wifi Setup..."
# fb_println "Installing Wireless Drivers..."
# mkdir -p /lib/modules/$(uname -r)/kernel/drivers/net/wireless
# cp /media/usb0/wifi/8812au.ko /lib/modules/$(uname -r)/kernel/drivers/net/wireless
# depmod -a
# fb_println "Installing Debian Packages..."
# cd $usb_dir/wifi
# dpkg -i -G -E libiw30_30~pre9-8_armel.deb wireless-tools_30~pre9-8_armel.deb libdbus-1-3_1.6.8-1+deb7u6_armel.deb libnl-3-200_3.2.7-4+deb7u1_armel.deb libnl-genl-3-200_3.2.7-4+deb7u1_armel.deb libpcsclite1_1.8.4-1+deb7u2_armel.deb libssl1.0.0_1.0.1t-1+deb7u2_armel.deb libtinfo5_5.9-10_armel.deb
# dpkg -i -G -E --ignore-depends initscripts wpasupplicant_1.0-3+deb7u4_armel.deb
# dpkg -i -G -E dhcpcd5_5.5.6-1+deb7u2_armel.deb

BASEDIR="$( cd "$( dirname "$0" )" && pwd )"
echo $BASEDIR

cd $BASEDIR/extra
fb_println "Additional Packages Installation..."
dpkg -i dos2unix_6.0-1_armel.deb
dpkg -i nano_2.2.6-1+b1_armel.deb

fb_println "Copying config files..."
# cp $BASEDIR/wpa_supplicant.conf /etc/
cp $BASEDIR/config/interfaces /etc/network/

fb_println "Wifi Installation Completed"

ifdown
ifup
ifconfig

fb_println "Configure SSH..."
cp $BASEDIR/config/sshd_config /etc/ssh/
chmod 644 /etc/ssh/ssh_config
chmod 644 /etc/ssh/ssh_host_dsa_key.pub
chmod 644 /etc/ssh/ssh_host_key.pub
chmod 644 /etc/ssh/ssh_host_rsa_key.pub
chmod 600 /etc/ssh/ssh_host_dsa_key
chmod 600 /etc/ssh/ssh_host_key
chmod 600 /etc/ssh/ssh_host_rsa_key
chmod 640 /etc/ssh/sshd_config
/usr/bin/ssh-keygen -t rsa
/usr/bin/ssh-keygen -t dsa

# ssh-keygen -y -t rsa -f /etc/ssh/ssh_host_rsa_key
# ssh-keygen -y -t dsa -f /etc/ssh/ssh_host_dsa_key
service ssh restart

fb_println "Setup Completed..."

#edit path /etc/udev/rules.d/70-persistent-net.rules



