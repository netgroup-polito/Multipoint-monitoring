# Packet loss measurements

### Dependencies

This test requires:
```
python2.7, openvswitch, mininet, net-tools, screen, networkx, zmq
```

On Fedora/Red Hat they can be installed with:
```sh
sudo dnf install python2 openvswitch net-tools screen
sudo pip install networkx pyzmq
mininet/util/install.sh -n
```

### Run the test
- First, start Open vSwitch running the following commands:
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

- Start the controller, choosing a topology from the "topologies" folder:
    ```sh
    screen -S controller -d -m python pox/pox.py Controller --topo=../topologies/[TOPOLOGY].graphml
    ```
- Start the Mininet script (using the same topology):
    ```sh 
    sudo python Net_Mininet.py ../topologies/[TOPOLOGY].graphml
    ```

