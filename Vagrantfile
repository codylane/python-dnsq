# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  config.vm.define 'default' do |config|
    config.vm.box = "debian/stretch64"
    config.vm.hostname = "vagrant-dnsq-01.foo-domain.com"

    # Vagrant >= 1.7 wants to replace the insecure_key with public boxes, but
    # there is a bug in that implentation so we just allow the insecure_key
    # anyway.
    config.ssh.insert_key = false

    config.vm.box_check_update = false

    config.vm.network "private_network", ip: "67.77.255.142"

    config.vm.synced_folder ".", "/vagrant",
      disabled: false,
      type: "sshfs",
      ssh_opts_append: "-o Compression=yes -o ControlPersist=60s -o ControlMaster=auto",
      sshfs_opts_append: "-o cache=no -o nonempty"

    config.vm.synced_folder ".", "/dnsq-build",
      type: "rsync",
      rsync__auto: true,
      rsync__chown: false,
      rsync__exclude: [
        'build/',
        'dist/',
        '__pycache__/',
        'tmp/',
        '*.egg-info/',
        '.git/',
        '.tox/',
        'inventory',
        '*.pyc',
        '*.retry',
        '*.built',
        '*.converged',
        '*.coverage',
      ]

    config.vm.provision "ansible" do |ansible|
      ansible.verbose = "v"
      ansible.playbook = "playbook.yml"
    end

    config.vm.provider "virtualbox" do |vb|
      #  # Display the VirtualBox GUI when booting the machine
      #  vb.gui = true

      vb.cpus = "1"
      vb.memory = "768"

      vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
      vb.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
    end
  end
end
