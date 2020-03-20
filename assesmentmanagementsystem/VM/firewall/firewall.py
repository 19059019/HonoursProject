import sys
import os
import socket

""" This must be run as root, or UFW must be allowed by non-root users """


class Firewall:
    def __init__(self):
        self.name = "firewall"

    def allow(target):
        os.system("ufw allow out to {}".format(socket.gethostbyname(target)))

    def block_all(self):
        os.system("ufw default deny outgoing")
        os.system("ufw default deny incoming")
        os.system("ufw default deny routed")

    def reset(self):
        # Reset and disable
        os.system("ufw --force reset")

    def allow_all(self):
        os.system("ufw default deny outgoing")
        os.system("ufw default deny incoming")
        os.system("ufw default deny routed")

    def allow_stellenbosch(self):
        self.enable()
        os.system("ufw allow out to {}".format("146.232.0.0/16"))

    def block_inetkey(self):
        os.system(
            "ufw deny out to {}".format(socket.gethostbyname("inetkey.sun.ac.za"))
        )
        os.system(
            "ufw deny in from {}".format(socket.gethostbyname("inetkey.sun.ac.za"))
        )
        os.system(
            "ufw deny out to {}".format(socket.gethostbyname("maties2.sun.ac.za"))
        )
        os.system(
            "ufw deny in from {}".format(socket.gethostbyname("maties2.sun.ac.za"))
        )

    def setup(self):
        # Block all by default
        self.block_all()
        # Allow DNS
        os.system("ufw allow out 53")
        os.system("ufw enable")

    def teardown(self):
        # Reset defaults to allow all
        self.allow_all()
        # Disable
        self.reset()


if __name__ == "__main__":
    firewall = Firewall()
    firewall.setup()
    firewall.teardown()
