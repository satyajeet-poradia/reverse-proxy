# reverse-proxy
this project implements a reverse tcp/http proxy with json confiugration file

# install dependencies
```shell
$ pip install peewee
```

# configuring json file
```json
{
    "proxy_server": "proxyserver_ip:proxyserver_port",                 
    "web_server": ["webserver_ip:webserver_port"],     
    "queue": "no_of_connections_in_queue",
    "max_data_receive": "maximum_no_of_bytes_receive",
    "api": ["api_endpoints"],
    "threshold": "threshold_time",                       
    "cache_timeout": "cache_timout_in_seconds"                           
}
```
Example config.json
```json
{
    "proxy_server": "0.0.0.0:8080",
    "web_server": ["google.com:80"],   
    "queue": 50,                                    
    "max_data_receive": 8192,                      
    "api": ["/api/v1/stats"],                       
    "threshold": 1.00001,
    "cache_timeout": 5                         
}
```
# start the reverse proxy

Edit a confiuration with format listed in the section "configuring json file" and start the app.py with option "--config":

```shell
$ python app.py --config my_config.json
```
# running application using shell script
Run Run.sh to run the application. Modify path in Run.sh to the dir of your app.
```shell
$ chmod a+x Run.sh
$ ./Run.sh
```

# testing
Run Test.sh to ensure system capabilities
```shell
$ chmod a+x Test.sh
$ ./Test.sh
```

 # logging
logs will be generated in reverseproxy.log file in your app directory



# License

Apache license 2.0
