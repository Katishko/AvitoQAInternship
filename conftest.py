import pytest
import random

@pytest.fixture(scope="session")
def base_url():
    return "https://qa-internship.avito.com"

@pytest.fixture(scope="session")
def headers():
    return {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

@pytest.fixture(scope="session")
def seller_id():
    # генерация sellerID
    return random.randint(111111, 999999)

@pytest.fixture(scope="session")
def created_items():
    # ОБЯЗАТЕЛЬНО session, иначе список будет пустой в каждом тесте
    return []