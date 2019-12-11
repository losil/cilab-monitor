#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CILAB term Paper task 15

Monitoring script written in python.

This scripts checks tcp ports of hosts. hosts and ports are provided in a yaml configuration file.
if the configured threshold is reached, a notifaction mail is sent.

Author: Silvan Loser (silvan.loser@stud.hslu.ch)
Date: 10.12.2019
Version: 1.0
"""

import os
import logging
import socket
import sys
import time
from email.headerregistry import Address
from email.message import EmailMessage
import smtplib
import ssl
from cryptography.fernet import Fernet
import yaml


"""
Vars
"""

CONFIG_FILE = "config.yml"
PASSWORD_FILE = "password.bin"
KEY_FILE = "key.bin"

"""
Classes
"""


class MailHandler(object):
    """
    A simple MailHandler.
    """

    def __init__(self, mail_config):
        """
        initializing important vars for login to mail provider.
        """
        self.sender_email = mail_config['from']
        self.receiver_email = ",".join(mail_config['to'])
        self.port = mail_config['port']
        self.smtp_server = mail_config['server']
        self.context = ssl.create_default_context()
        self.password = decrypt_password()

    def __send_mail(self, host, port, state):
        """
        private method to avoid a lot of duplicate code.
        """
        if state == "down":
            message_text = "Port {0} on Host {1} is down! Please check your system!".format(
                port, host)
        else:
            message_text = "Port {0} on Host {1} is up! Your system has recovered!".format(
                port, host)

        self.message = "\r\n".join([
            "From: {0}".format(self.sender_email),
            "To: {0}".format(self.receiver_email),
            "Subject: Port {0} on Host {1} is {2}!".format(port, host, state),
            "",
            message_text
        ])

        # sending mails securely via starttls
        with smtplib.SMTP(self.smtp_server, self.port) as server:
            server.ehlo()
            server.starttls(context=self.context)
            server.ehlo()
            server.login(self.sender_email, self.password)
            server.sendmail(self.sender_email,
                            self.receiver_email, self.message)

    def send_mail_down(self, host, port):
        """
        public method for sending host is down notifications
        """
        self.__send_mail(host, port, "down")

    def send_mail_up(self, host, port):
        """
        public method for sending host has recoverd notifications
        """
        self.__send_mail(host, port, "up")


class ConfigLoader(object):
    """A simle config loader."""

    def __init__(self, config_file):
        """
        reads config file from filesytem
        raises expetion if yaml is malformatted.
        """
        with open(config_file, 'r') as stream:
            try:
                self.config = (yaml.safe_load(stream))
            except yaml.YAMLError as ecx:
                raise ecx

    def get_config(self):
        """
        returns config in a dict
        """
        return self.config


class Logger(object):
    """ class that returns configured Logger. """

    def __init__(self):
        """
        initializes logger object with correct settings
        """
        self.logger = logging.getLogger("monitor.py")

        # create handlers
        self.c_handler = logging.StreamHandler()
        self.c_handler.setLevel(logging.DEBUG)

        # Create formatters and add it to handlers
        self.logging_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.c_handler.setFormatter(self.logging_format)

        # Add handlers to the logger
        self.logger.addHandler(self.c_handler)

    def get_logger(self):
        """
        returns configured logging object
        """
        return self.logger


"""
Functions
"""


def check_hostnames(hostnames):
    """
    checks if hosts can be resolved and are valid
    """
    for hostname in hostnames:
        try:
            socket.gethostbyname(hostname)
        except socket.error:
            LOGGER.error("cannot resolve " + hostname)
            LOGGER.error("check your configuration")
            sys.exit(1)


def check_host(hostname, ports, mail_handler, max_failures):
    """
    Checks a specific host on ports which are provided in a list
    """

    for port in ports:
        LOGGER.debug("checking host {0} on port {1}".format(hostname, port))

        # setting up name of the temporary state file which can be used
        host_status_file = "/tmp/{0}.{1}.tmp".format(hostname, port)
        try:
            # open socket to given host and tcp port
            # timeout is used to avoid false failures if there is some latency
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((hostname, port))

            # check if host was down at last check, inform with notification and cleanup state file
            if os.path.isfile(host_status_file):
                mail_handler.send_mail_up(hostname, port)
                LOGGER.debug("notification about recovery has been sent!")
                os.remove(host_status_file)

            LOGGER.info("Port {0} on {1} is up!".format(port, hostname))
            sock.shutdown(socket.SHUT_RDWR)
        except:
            LOGGER.error("Port {0} is down on {1}".format(port, hostname))

            if os.path.isfile(host_status_file):
                # host already down
                failed_checks = int(open(host_status_file).read())

                # check if number of downstate has reached the threshold
                # if yes notification mail is sent
                if failed_checks == max_failures:
                    mail_handler.send_mail_down(hostname, port)
                    LOGGER.debug(
                        "mail with downstate information has been sent")

                # increate down counter in file
                open(host_status_file, 'w').write(str(failed_checks + 1))
            else:
                # increase down counter in file
                open(host_status_file, 'w').write(str(1))

        finally:
            # closing open socket at the end of every checked port
            sock.close()


def decrypt_password():
    """
    Decrypting password which is used for login on gmail servers.
    """

    # reading bytes streams from files
    with open(PASSWORD_FILE, 'rb') as password_file:
        encrypted_password = password_file.read()
        password_file.close()
    with open(KEY_FILE, 'rb') as key_file:
        key = key_file.read()
        key_file.close()

    # decrypt ciphered text
    cipher_suite = Fernet(key)
    unciphered_text = cipher_suite.decrypt(encrypted_password)
    LOGGER.debug("password successfully decrypted")
    return bytes(unciphered_text).decode("utf-8")


""""
initialize global logging environment
"""
CONFIG = ConfigLoader(CONFIG_FILE).get_config()
LOGGER = Logger().get_logger()

if CONFIG["log_level"] == 'info':
    LOGGER.setLevel(logging.INFO)
else:
    LOGGER.setLevel(logging.DEBUG)


def main():
    """
    Main function
    """
    check_interval = CONFIG['check_interval']
    mail_handler = MailHandler(CONFIG["mail"])

    check_hostnames(CONFIG['hosts'].keys())
    while True:
        for host in CONFIG['hosts'].keys():
            check_host(host, CONFIG['hosts'][host],
                       mail_handler, CONFIG["max_failures"])
        time.sleep(check_interval)

    sys.exit(0)


if __name__ == "__main__":
    main()
