# Packet loss measurements

### Dependencies

This test requires:
```
python2.7, openvswitch, mininet, net-tools, screen, python-devel, tkinter, networkx(v>=2.0), zmq, matplotlib
```

On Fedora/Red Hat they can be installed with:
```sh
sudo dnf -y install python2 openvswitch net-tools screen zeromq python-devel tkinter redhat-rpm-config
sudo pip install networkx zmq matplotlib
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
    screen -S controller -d -m python pox/pox.py Controller --topology=../topologies/<TOPOLOGY>.graphml [--IPsrc=<x.x.x.x> --IPdst=<x.x.x.x> --MACsrc=<XX:XX:XX:XX:XX:XX> --MACdst=<XX:XX:XX:XX:XX:XX>] openflow.discovery
    ```
- Start the Mininet script (using the same topology):
    ```sh 
    sudo python Network_sim.py ../topologies/<TOPOLOGY>.graphml
    ```
- The Mininet script starts the packet generator `Client.py` in each host. This script sends a report to the collector `Server.py`, which writes the amount of sent/received files in `results.dat` and `summary.dat`. You can monitor the summary file with:
    ```sh
    watch "cat summary.dat |tail"
    ```
    At the end of the test, `Server.py` writes in `summary.dat` the total amount of packets sent, received and lost. This values can be compared with the measured obtained with the alternate marking method implemented in the controller.
- At the end of the test, stop the controller with:
    ```sh
    screen -S controller -X stuff ^C
    ```
  The controller saves in `results.json` the per-period measurements. 
- You can plot the amount of measured lost packets with:
    ```sh
    python plot.py
    ```
