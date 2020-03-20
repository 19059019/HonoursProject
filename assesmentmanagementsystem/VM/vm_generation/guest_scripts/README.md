# Guest Scripts
These scripts will make a symbolic link to the shared folder and store it in the home directory of the logged in user. These scripts were tested with Ubuntu 16.04.

The _profile_ script should be stored in /etc/profile in the virtual machines student account. This instructs the system to run the shared folder set up script when a student logs in.

The _link_shared.sh_ script must be stored in /opt and given the ability to perform actions as root. This can be done by an admin with the following command.

```
sudo chmod u+s link_shared.sh
```