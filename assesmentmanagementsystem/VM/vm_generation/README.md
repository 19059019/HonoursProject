# VM Generation

## Generate Virtual Machine

You can use _genVM.py_ to create a Virtual Machine from a setup JSON file that is given as the first argument. This script makes use of VBoxManage.

### Usage
```
Python3 genVM.py <setup.json>
```

## Set Up Virtual Machine

Once the virtual machine has been created, an admin must install the required operating system and prepare the student profiles. There must be a way for the students to clearly and obviously see a shared folder if one has been included. The Virtual machine must then be exported to OVF format and stored with all of the other OVF files. The new virtual machine must then manually added as an operating system option in the assignment creation page of the web application.

The _guest_scripts_ directory contains scripts to meet these requirements in an Ubuntu 16.04 system and instructions on how to use them.