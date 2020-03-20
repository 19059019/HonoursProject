from yaml import safe_load, dump

image = "python:3.5"
test_file = "test_wololo.py"

ci = ""
with open("ci_template.yml", "r") as temp:
    ci = safe_load(temp)
    ci["image"] = image
    ci["test"]["script"] = ["python {}".format(test_file)]
    with open("template.yml", "w") as target:
        dump(ci, target)

