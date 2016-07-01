# Solenoid
### Route Injection Agent
##### Author: Lisa Roach
##### Contact: Please use the Issues page to ask questions or open bugs and feature requests. 

## Description:

The end goal of this Route injector app is to be able to take any given logic and 
make changes to the prefixes on a RIB table.

The changes to the RIB are accomplished by using RESTconf calls to send JSON modeled by YANG. The YANG model I am currently using is [Cisco-IOS-XR-ip-static-cfg] (https://github.com/YangModels/yang/blob/master/vendor/cisco/xr/600/Cisco-IOS-XR-ip-static-cfg.yang). This model will likely change in the future, see Limitations.

For reading BGP changes I am using [exaBGP] (https://github.com/Exa-Networks/exabgp). Exabgp allows me to monitor BGP network announcements, withdrawals, etc. and trigger the RESTconf changes based on these updates. exaBGP acts completely as a listener, if you with to send BGP updates directly to Solenoid that should work as well (examples and documentation coming soon)

### Work in Progress:

Vagrant box demo scenario. 

Test at scale.

Change from RESTconf backend to [gRPC](http://www.grpc.io/docs/tutorials/basic/python.html) for enhanced performance.

#### Current Limitations:

As of now, the IOS-XR 6.0 device I am using does not have completed YANG models
for BGP RIB changes. As a temporary workaround, I can only add static routes
to the RIB.


### Usage:

Step 1: Clone this repo and cd into Solenoid.

Step 2: Export the following PYTHONPATH: ```export PYTHONPATH=$PYTHONPATH:lib/``` 

Step 3: Run ```python setup.py install``` to install the Solenoid application. 

Step 4 : Create a solenoid.config file in your top-level solenoid directory and fill in the values in the key:value pair. (If you are running this in an IOS-XR container, your IP address should be the loopback address in use for your container):

```
[default] # Or whatever you want to name this section, it maybe helpful to name it the router you are working on
ip: ip_address
port: port number
username: username
password: password
```

Step 5 (optional): Create a filter.txt file to include the ranges of prefixes to be filtered with. Single prefixes are also acceptable. Example:

```
1.1.1.0/32-1.1.2.0/32
10.1.1.0/32-10.1.5.0/32
10.1.1.6/32
192.168.1.0/28-192.168.2.0/28
```

Step 6: Set up [exaBGP] (https://github.com/Exa-Networks/exabgp). Form a neighborship with your BGP network. 

Step 7: Make sure RESTconf calls are working from your device to the RIB table

Example test (you should receive your device's whole configuration):

```
curl -X GET -H "Accept:application/yang.data+json,application/yang.errors+json" -H "Authorization: <INSERT YOUR AUTH CODE>" http://<YOUR IP>/restconf/data/?content=config
```

Step 8: Change your exaBGP configuration file to run the edit_rib.py script. The important part is the process monitor-neighbors section, the rest is basic exaBGP configuration.


Example:

```
group test {
        router-id x.x.x.x;

        process monitor-neighbors {
            encoder json;
            receive {
                parsed;
                updates;
                neighbor-changes;
            }
            run /your/python/location /path/to/solenoid/solenoid/edit_rib.py;
        }

        neighbor y.y.y.y {
            local-address x.x.x.x;
            local as ####;
            peer-as ####;
        }

}

```

If you chose to add a filter file, you must add the path to the file in the run call with the file flag -f (be sure to include the quotes):

```
run /your/python/location /path/to//solenoid/solenoid/edit_rib.py -f '/path/to/filter/file';
```

Step 9: Launch your exaBGP instance. You should see the syslog HTTP status codes if it is successful. 
