#!/usr/bin/env python3

# Internal packages
import random
from uuid import uuid4


def create_unique_id() -> str:
    return str(uuid4())


def create_unique_id_int(length: int = 32) -> int:
    return random.getrandbits(length)
