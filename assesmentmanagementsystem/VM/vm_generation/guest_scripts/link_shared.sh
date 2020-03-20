#! /bin/sh -e
# This script should be stored in /opt
# This must be given suid status with 'chmod u+s link_shared.sh' 
rm -rf ~/shared 2> /dev/null
mkdir ~/shared 2> /dev/null
ln -s /media/sf_sharedFolder ~/shared 2> /dev/null
chmod a+rwx /media/sf_sharedFolder
