Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-18.04"
  #
  # Run Ansible from the Vagrant Host
  #
  config.vm.provision "ansible_local" do |ansible|
    ansible.playbook = "ansible/setup.yml"
    ansible.install_mode = "pip"
  end
  config.vm.network "forwarded_port", guest: 5433, host: 5433
  config.vm.network "forwarded_port", guest: 8081, host: 8081
  config.vm.network "forwarded_port", guest: 8882, host: 8882
  config.vm.network "forwarded_port", guest: 5673, host: 5673
  config.vm.network "forwarded_port", guest: 6380, host: 6380
  config.vm.network "forwarded_port", guest: 5002, host: 8002
  config.vm.network "forwarded_port", guest: 5001, host: 8001
end
