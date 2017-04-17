# vagrant-boxes

## idm

Example vagrant boxes and Ansible role to setup openldap server.

SSH config should be placed in `.ssh/config` file:

```
Host test1
  HostName 127.0.0.1
  User vagrant
  Port 2222
  UserKnownHostsFile /dev/null
  StrictHostKeyChecking no
  PasswordAuthentication no
  IdentityFile /home/majimenez/Projects/vagrant-test/.vagrant/machines/test1/virtualbox/private_key
  IdentitiesOnly yes
  LogLevel FATAL

Host test2
  HostName 127.0.0.1
  User vagrant
  Port 2200
  UserKnownHostsFile /dev/null
  StrictHostKeyChecking no
  PasswordAuthentication no
  IdentityFile /home/majimenez/Projects/vagrant-test/.vagrant/machines/test2/virtualbox/private_key
  IdentitiesOnly yes
  LogLevel FATAL
```

Run example with:

`$ ansible-playbook -i hosts idm.yml`
