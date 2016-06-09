# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.box = "fedora/23-cloud-base"
  config.vm.network "forwarded_port", guest: 8000, host: 8087
  config.vm.synced_folder ".", "/code"

  config.vm.provider "virtualbox" do |vb|
    vb.memory = "1024"
  end

  config.vm.provision "shell", privileged: false, inline: <<-SHELL
    sudo dnf install -y git ctags python-virtualenv python-devel gcc \
      mariadb-server mariadb-devel \
      redhat-rpm-config

    # create development environment and install dependencies
    virtualenv nitrate-env
    . ~/nitrate-env/bin/activate
    pip install -r /code/requirements/devel.txt
    cd /code
    python setup.py develop
    deactivate

    # setting up database
    sudo systemctl enable mariadb.service
    sudo systemctl start mariadb.service

    echo "create database nitrate character set utf8" | mysql -uroot
    cd /code/contrib/sql
    mysql -uroot nitrate < nitrate_db_setup.sql
    cd /code/contrib/sql/migrate
    mysql -uroot nitrate < nitrate_db_upgrade_v3.8.8-1_v3.8.9-1.sql
    mysql -uroot nitrate < nitrate_db_upgrade_v3.8.9-1_v3.8.10-1.sql
    mysql -uroot nitrate < nitrate_db_upgrade_v3.8.10-1_v3.8.11-1.sql

    echo "CREATE USER 'nitrate'@'localhost' IDENTIFIED BY 'nitrate'" | mysql -uroot
    echo "GRANT ALL ON nitrate.* TO 'nitrate'@'localhost'" | mysql -uroot

    # test for verifying whether user nitrate works
    echo 'select "hello world"' | mysql -unitrate -pnitrate nitrate

    # load fixtures into database
    . ~/nitrate-env/bin/activate
    django-admin.py loaddata --settings=tcms.settings.devel /code/contrib/sql/initial_data.json
    deactivate

    cd
  SHELL
end
