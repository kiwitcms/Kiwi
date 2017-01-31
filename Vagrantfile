# -*- mode: ruby -*-
# vi: set ft=ruby :


Vagrant.configure(2) do |config|
  config.vm.box = "fedora/25-cloud-base"
  config.vm.network "forwarded_port", guest: 8000, host: 8087
  config.vm.synced_folder ".", "/code"

  config.vm.provider "virtualbox" do |vb|
    vb.memory = "1024"
  end

  config.vm.provision "mysql", privileged: true, type: "shell", inline: <<-SHELL
    dnf install -y mariadb-server mariadb-devel

    systemctl enable mariadb.service
    systemctl start mariadb.service

    echo "create database nitrate character set utf8" | mysql -uroot

    echo 'select "hello world"' | mysql -uroot nitrate
  SHELL

  config.vm.provision "pgsql", privileged: true, type: "shell", inline: <<-SHELL
    dnf install -y postgresql-server postgresql postgresql-devel
    postgresql-setup --initdb
    systemctl enable postgresql.service
    systemctl start postgresql.service
  SHELL

  config.vm.provision "deps", privileged: true, type: "shell", inline: <<-SHELL
    dnf install -y git ctags redhat-rpm-config ipython python-ipdb

    # Required to build environment to develop and run Nitrate
    dnf install -y python-devel gcc

    # Some of dependent packages cannot be installed from PyPI. Hence, install
    # those packages from Fedora repository.
    dnf install -y kobo-django
  SHELL

  config.vm.provision "docker", privileged: true, type: "shell", inline: <<-SHELL
    dnf install -y docker
    systemctl enable docker
    systemctl start docker
    groupadd docker
    usermod -aG docker $USER
    systemctl restart docker
  SHELL

  config.vm.provision "rpmutils", privileged: true, type: "shell", inline: <<-SHELL
    dnf install -y rpm-build rpmlint rpmdevtools
  SHELL

  config.vm.provision "devenv", privileged: false, type: "shell", inline: <<-SHELL
    cd
    sudo dnf install -y python2-virtualenv

    virtualenv --system-site-packages nitrate-env
    . ~/nitrate-env/bin/activate
    pip install -r /code/requirements/devel.txt
    cd /code
    python setup.py develop
    deactivate
    cd
  SHELL
end
