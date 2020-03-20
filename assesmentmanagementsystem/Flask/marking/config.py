import configparser

config = configparser.ConfigParser()
config.read("resources/config.ini")
tokens = config["Tokens"]