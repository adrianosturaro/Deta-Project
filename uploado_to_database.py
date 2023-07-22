import database as db
import streamlit_authenticator as stauth
from typing import List

usernames: List[str] = ["pparker", "rmiller"]
names: List[str] = ["Peter Parker", "Rebecca Miller"]
passwords: List[str] = ["abc123", "cdf456"]
hashed_passwords: List[str] = stauth.Hasher(passwords=passwords).generate()

for username, name, hash_password in zip(usernames, names, hashed_passwords):
    db.insert_user(username=username, name=name, password=hash_password)
