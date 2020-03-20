import configparser

config = configparser.ConfigParser()
config.read("resources/config.ini")
tokens = config["Tokens"]

config = configparser.ConfigParser()
config.read("resources/.email_config.ini")