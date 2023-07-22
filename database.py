"""Exemplifica o uso de uma banco de dados Deta https://deta.space/"""

from __future__ import annotations
import os
from dotenv import load_dotenv
from deta import Deta
from typing import List, Dict, Any

# Load de env variables
load_dotenv(".env")
DETA_KEY = os.getenv("DETA_KEY")


class UserNotFound(Exception):
    def __init__(self, mensagem: str) -> None:
        self.mensagem = mensagem
        super().__init__(mensagem)


deta: Deta = Deta(DETA_KEY)  # Conecta ao Deta

db = deta.Base("Streamlit_App")  # Cria o banco de dados


def insert_user(username: str, name: str, password: str):
    """insere um novo usuário no baco de dados"""
    db.put({"key": username, "name": name, "password": password})


def fetch_all_users() -> List[Dict[str, str]]:
    """Recupera todos os usuários"""
    res = db.fetch()
    return res.items


def get_user(username: str) -> Dict[str, str] | None:
    """Retorna os dados com base no nome do usuário"""
    return db.get(key=username)


def update_user(username: str, updates) -> None:
    """Atuliza um usuário om base em um dicionário"""
    if db.get(key=username) is None:
        raise UserNotFound(mensagem=f"Usuário {username} não encontrado") from None
    return db.update(updates=updates, key=username)


def delete_user(username: str) -> None:
    return db.delete(key=username)


if __name__ == "__main__":

    insert_user(username="pparker", name="Peter Parker", password="abc123")

    print(fetch_all_users())

    print(get_user("pparker"))

    update_user(username="pparker", updates={"password": "abc124"})

    print(get_user("pparker"))

    delete_user("pparker")

    print(get_user("pparker"))
