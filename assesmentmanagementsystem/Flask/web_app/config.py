import configparser

config = configparser.ConfigParser()
config.read("resources/config.ini")
# Change per place
config = config["sun"]
locks = {}

 