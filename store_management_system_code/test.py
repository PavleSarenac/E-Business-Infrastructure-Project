import json

json_string = '{\n  "version": 3,\n  "id": "a1a5d9c9-4ff2-4bf7-a67f-48a8db82f9d1",\n  "address": "b0df78c759c9029da1cc0197403c37c89623c0da",\n  "Crypto": {\n    "ciphertext": "5497863151ec366498b9a26e6626da0ae9623eaf57c37a7090bfb1ad3e17e2a4",\n    "cipherparams": {\n      "iv": "5dd70e479de799cfad089cb751d0d8ad"\n    },\n    "cipher": "aes-128-ctr",\n"kdf": "scrypt",\n    "kdfparams": {\n      "dklen": 32,\n      "salt": "50dd86a6fd0b1c0b2164af06f73151cc323604608533d41ab0354489018e14bc",\n      "n": 8192,\n      "r": 8,\n      "p": 1\n    },\n    "mac": "6910ae96ec91835c32a48f069a4879e7f4482ecc05c22b60214b70f53aa66b68"\n  }\n}'

print(json_string)

# Convert the JSON string to a Python dictionary
data_dict = json.loads(json_string.replace("'", '"'))

print(data_dict)
