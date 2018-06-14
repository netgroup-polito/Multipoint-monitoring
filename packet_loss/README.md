# Packet loss measurements

### Dependencies

This test requires:
```
python2.7, openvswitch, mininet, net-tools, screen, networkx(v>=2.0), zmq
```

On Fedora/Red Hat they can be installed with:
```sh
sudo dnf install python2 openvswitch net-tools screen zeromq
sudo pip install networkx zmq
mininet/util/install.sh -n
```

### Run the test
- First, start Open vSwitch running the following commands:
   ```sh
   sudo systemctl enable openvswitch.service
   sudo systemctl start openvswitch.service
   ```
   Alternatively, Open vSwitch can be started manually with:
   ```sh
   sudo ovsdb-tool create
   sudo ovsdb-server --remote=punix:/var/run/openvswitch/db.sock \
            --remote=db:Open_vSwitch,Open_vSwitch,manager_options \
            --private-key=db:Open_vSwitch,SSL,private_key \
            --certificate=db:Open_vSwitch,SSL,certificate \
            --bootstrap-ca-cert=db:Open_vSwitch,SSL,ca_cert \
            --pidfile --detach --log-file
    sudo ovs-vsctl --no-wait init
    sudo ovs-vswitchd --pidfile --detach --log-file
    ```
- Start the controller, choosing a topology from the "topologies" folder and, optionally, setting the addresses to select the monitored flow:
    ```sh
    screen -S controller -d -m python pox/pox.py Controller --topo=../topologies/<TOPOLOGY>.graphml [--IPsrc=<x.x.x.x> --IPdst=<x.x.x.x> --MACsrc=<XX:XX:XX:XX:XX:XX> --MACdst=<XX:XX:XX:XX:XX:XX>] openflow.discovery
    ```
- Start the Mininet script (using the same topology):
    ```sh 
    sudo python Network_sim.py ../topologies/<TOPOLOGY>.graphml
    ```

