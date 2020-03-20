# This does not block google drive or docs
echo $1 | sudo -S bash -c "cat google_domains.txt >> /etc/hosts"
