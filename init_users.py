# init_users.py

import json
from auth import hash_password

users = {
    "deepika@1acre.in": hash_password("deepika@1acre"),
    "sandeep@1acre.in": hash_password("1acre@sandeep"),
    "satish@1acre.in": hash_password("1acre@satish"),
    "pavan@1acre.in": hash_password("1acre@pavan")

}

with open('users.json', 'w') as f:
    json.dump(users, f)

print("users.json initialized successfully.")