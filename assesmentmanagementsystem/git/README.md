# Gitlab setup instructions
### Install Dependencies (Posix not required):
```
sudo apt update
sudo apt upgrade
sudo apt-get install ca-certificates curl openssh-server
```
### Link the repository:
```
cd /tmp
curl -LO https://packages.gitlab.com/install/repositories/gitlab/gitlab-ce/script.deb.sh
sudo bash script.deb.sh
```
### Install Gitlab:
```
sudo apt-get install gitlab-ce
```
### Configure Gitlab:
```
sudo vim /etc/gitlab.gitlab.rb
```
Find the line with external_url 'https://yourdomain' replace 'yourdomain' with the IP address that you would like to expose the server on.
### Reconfigure Gitlab:
This exposes gitlab on the given IP address. It will take a while.
```
sudo gitlab-ctl reconfigure
```

You can now reach you server at the given IP address on the network or from the localhost on your pc. The first time you open it, you will be prompted to enter an admin password. You will then be able to log in with username *admin@example.com* and the password that you have just set.

### Allow local requests
If you are using a gitlab instance on the same host as your webserver, you will need to go to /admin/application_settings/network on you git instance and “Allow requests to the local network from hooks and services” in the “Outbound requests” section. THIS IS VERY INSECURE AND NOT RECOMENDED.

ENJOY!

# Assessment Management System Instructions
The git server and token are stored in the config.ini file in the webapp. Create a new profile with your API token for this instance of gitlab in the config file and change the profile that is being used in the config.py file.
