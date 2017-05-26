# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-16.04"
  config.ssh.username = "vagrant"
  config.ssh.password = "vagrant"
  config.vm.provision :shell, path: "bootstrap.sh"
  config.vm.network :forwarded_port, guest: 8888, host: 8888
  config.vm.provision "shell", run: "always", privileged: false, inline: <<-SHELL
    jupyter notebook --config=/vagrant/jupyter_notebook_config.py &
  SHELL
  config.vm.provider "virtualbox" do |v|
    # v.gui = true
    v.memory = 2048
    v.cpus = 4
  end
end
