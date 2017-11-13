""" 
A server that acts as a proxy service 
"""


"""
Import all required libraries 
"""
import logging
import argparse
import sys
import json
import socket
import thread
import os
import re
import time
import models
from peewee import *
import cache


def get_host_port_tupple(server):
    """ 
    A function that converts server address to a tupple
    containing host and port number
    :return: Tupple (HOST, PORT). For example ('localhost', 80)
    """ 
    if ':' in server:
        server = server.split(':')
        # Return ('0.0.0.0', 80)
        return (server[0], int(server[1]))


def create_request(request, config):
    """
    A function that creates a request based to client request.
    This function replaces proxy host with web server host
    :return: HTTP request
    """
    # Get web server info
    web_server = get_host_port_tupple(config['web_server'][0])

    # Generate web host string
    web_host = "Host: " + web_server[0] + ":" + str(web_server[1])

    # Split request
    request = request.splitlines()

    try:
        if request:
            # In valid request change the Host to web host
            if 'Host' in request[1]:
                request[1] = web_host
            
            # Return generated request
            return ("\r\n".join(request) + "\r\n", request[0].split(' ')[1])
    except:
        return

def create_response(response):
    """
    A funtion that creates a response message with appropriate headers.
    return: status, headers, response
    """
    # Convert dictionary to json
    res = json.dumps(response)

    # Set Response headers
    response_headers = {
        'Content-Type': 'application/json; encoding=utf8',
        'Content-Length': len(res.encode(encoding="utf-8")),
        'Connection': 'close',
    }

    # Format resposne  headers
    response_headers_raw = ''.join('%s: %s\n' % (k, v) for k, v in response_headers.items())

    # Set HTTP version, status code and status
    response_proto = 'HTTP/1.1'
    response_status = '200'
    response_status_text = 'OK' # this can be random

    # Format data
    r = '%s %s %s' % (response_proto, response_status, response_status_text)
    
    return r, response_headers_raw, res

def start_proxy_server(config):
    """
    A function that starts the server.
    This function creates a socket and binds it to the proxy server.
    The server keeps on listening to the incoming connections
    :return: None
    """
    if config:
        # Get proxy server (HOST, PORT)
        proxy_server = get_host_port_tupple(config['proxy_server'])

        # Initialize redis server
        try:
            cache_requests = cache.CacheList()
        except Exception as error:
            print error

        try:
            # Create a socket for proxy server
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Reuse the address
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind address, port to socket
            s.bind(proxy_server)

            # Start listening for clients
            s.listen(config['queue'])

            logging.info("Proxy server running on %s:%s", proxy_server[0], proxy_server[1])
        except socket.error, (value, message):
            if s:
                # if the socket is created and found error, close socket
                s.close()
            logging.error("Could not open socket: %s", message)
            # Exit
            sys.exit(1)

        while True:
            # Get client info
            conn, client_addr = s.accept()
            logging.info("Accepted a connection from %s", client_addr)
            try:
                # Start new thread for each connected client
                thread.start_new_thread(proxy_thread, (conn, client_addr, config, cache_requests))
            except Exception as Error:
                print Error
        s.close()

def proxy_thread(conn, client_addr, config, cache_requests):
    """
    A function that intiates a Thread each time client has connected to the Proxy server.
    This function modifies the client request and sends it to web server.
    After getting response from the webserver it sends the response to client.
    :return: None
    """

    # Get a request from browser
    request = conn.recv(999999)
    request_time = time.time()


    try:
        # Parse the server request
        server_request = create_request(request, config)

        # Check if stats api
        if server_request[1] in config['api']:

            # Initialize response objects
            response = dict()
            quries = dict()
            slow_requests = dict()

            # Get all records with count
            for record in models.Details.select(models.Details.url, fn.Count(models.Details.url).alias('count')).group_by(models.Details.url):
                quries[record.url] = record.count

            # Get all records that took more than threshold time
            for record in models.Details.select().where(time > config['threshold']):
                slow_requests[record.url] = record.time
            
            # Bind both responses to response object
            response['quries'] = quries
            response['slow_requests'] = slow_requests

            # Construct a HTTP JSON Resposne
            r, response_headers_raw, res = create_response(response)

            #send Response to the browser
            conn.send(r.encode(encoding="utf-8"))
            conn.send(response_headers_raw.encode(encoding="utf-8"))
            conn.send('\n'.encode(encoding="utf-8"))
            conn.send(res.encode(encoding="utf-8"))

        # Check if requested URL already in cache
        elif cache_requests.get_entry(server_request[1]):
            # Get Response
            response = cache_requests.get_entry(server_request[1])
            #send Response
            conn.send(response)
            try:
                # Enter a record to Database
                models.Details.create(url = str(server_request[1]), time = time.time() - request_time, dt = time.time())
            except Exception as error:
                pass
        else:
            # Create a socket for web server
            web_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

            # Bind socket to web server 
            hip = socket.gethostbyname('webservices.nextbus.com')
            web_socket.connect((hip, 80))
            web_socket.send(server_request[0])

            # set socket non blocking
            web_socket.setblocking(0)

            # variables for generating data
            total_data=[]
            data=''
            begin = time.time()
            timeout = 2


            while 1:
                # If data exist than break after timeout
                if total_data and time.time() - begin > timeout:
                    break

                # If no data than wait for longer period
                elif time.time() - begin > timeout * 2:
                    break

                try:
                    # Receive data in chunks
                    data = web_socket.recv(config['max_data_receive'])

                    if data:
                        # Collect all data
                        total_data.append(data)

                        # Change the beginning time for measurement
                        begin = time.time()
                    else:
                        # Sleep for sometime
                        time.sleep(0.1)
                except:
                    pass

            try:
                # Enter a record to Database
                models.Details.create(url = str(server_request[1]), time = time.time() - request_time, dt = time.time())
            except Exception as error:
                pass
    
            # Send all data to browser
            conn.send("".join(total_data))

            # Cache
            try:
                ca = cache.Cache(server_request[1], "".join(total_data), config['cache_timeout'])
                cache_requests.add_entry(ca)
            except Exception as error:
                print error

            # Close web socket
            web_socket.close()

    except Exception as error:
        pass

    conn.close()

def parse_args():
    """
    A function to parse the config.json file.
    :return: Object config 
    """
    parser = argparse.ArgumentParser(description = "Reverse Proxy Service ThousandEyes")
    # Parse information from config file
    parser.add_argument('--config', dest = 'config_file', help = 'Configuration file')
    return parser.parse_args( sys.argv[1:] )

def load_config(config_file):
    """
    A function to load the config file.
    :return: JSON fomratted config
    """
    logging.info("Loading config file %s", config_file)
    with open(config_file) as f:
        return json.load(f)
    return None

def main():
    """
    A function to bootstrap the application.
    This function loads the config.json file anf runs the proxy server.
    :return: None
    """
    # Initialize log file
    logging.basicConfig(filename='reverseproxy.log', level= logging.DEBUG)

    args = parse_args()
    # Check if config file provided
    if args.config_file:
        # Get data from config file
        config = load_config(args.config_file)
        try:
            # Start the proxy server
            start_proxy_server(config)
        except:
            logging.error("Failed to start server %s", config['proxy_server'])


"""
Calling main()
"""
if __name__=="__main__":
    # Initialize data base
    models.initialize()

    # Bootstrap server
    main()