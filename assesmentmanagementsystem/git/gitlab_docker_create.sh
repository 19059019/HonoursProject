sudo docker run --detach --name gitlab --hostname git.ams.sun.ac.za --publish 30080:30080 --publish 30022:22 --env GITLAB_OMNIBUS_CONFIG="external_url 'http://146.232.213.15:30080'; gitlab_rails['gitlab_shell_ssh_port']=30022;" gitlab/gitlab-ce:latest