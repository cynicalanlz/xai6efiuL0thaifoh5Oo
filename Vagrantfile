Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-18.04"
  #
  # Run Ansible from the Vagrant Host
  #
  config.vm.provision "ansible_local" do |ansible|
    ansible.playbook = "ansible/setup.yml"
    ansible.install_mode = "pip"
  end
  config.vm.network "forwarded_port", guest: 8889, host: 8889
end
