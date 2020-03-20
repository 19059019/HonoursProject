touch temp_hosts
echo 127.0.0.1 localhost > temp_hosts
echo 127.0.1.1    $HOSTNAME >> temp_hosts
cat generic_hosts >> temp_hosts
echo $1 | sudo -S bash -c "cp temp_hosts /etc/hosts"
rm temp_hosts
