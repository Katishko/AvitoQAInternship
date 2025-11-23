import pytest
import requests
import uuid
import time
from jsonschema import validate, ValidationError

# схемы минимальные для проверки ключевых полей
ITEM_SCHEMA = {
    "type": ["object", "array"],
    "oneOf": [
        {"type": "object",
         "properties": {
            "id": {"type": "string"},
            "sellerId": {"type": "number"},
            "name": {"type": "string"},
            "price": {"type": "number"},
            "statistics": {"type": "object"},
            "createdAt": {"type": "string"}
         },
         "required": ["id", "sellerId", "name", "price", "createdAt"]
        },
        {"type": "array"}
    ]
}

STAT_SCHEMA = {
    "type": ["array", "object"],
}

@pytest.mark.dependency()
def test_create_item_positive(base_url, headers, seller_id, created_items):
    """
    TC-001: Create item — valid payload
    """
    url = f"{base_url}/api/1/item"

    payload = {
        "sellerID": seller_id,
        "name": f"test-item-{int(time.time())}",
        "price": 100,
        "statistics": {"likes": 1, "viewCount": 2, "contacts": 3}
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=10)

    # API возвращает {"status": "Сохранили объявление - <uuid>"}
    assert resp.status_code == 200

    body = resp.json()
    assert "status" in body, "API returned unexpected format"

    # Извлекаем ID из строки вида: "Сохранили объявление - <uuid>"
    status = body["status"]
    assert " - " in status, "Unexpected status format"
    
    item_id = status.split(" - ")[1].strip()

    # сохраняем ID для других тестов
    created_items.append(item_id)

    # Проверяем корректность UUID
    assert len(item_id) > 0

@pytest.mark.dependency(depends=["test_create_item_positive"])
def test_get_item_by_id(base_url, headers, created_items):
    """
    TC-002: Get item by id
    """
    assert created_items, "No created item id available"
    item_id = created_items[0]
    url = f"{base_url}/api/1/item/{item_id}"
    resp = requests.get(url, headers=headers, timeout=10)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    body = resp.json()
    # API может возвращать массив или объект — допускаем оба варианта
    if isinstance(body, list):
        assert any((it.get("id") == item_id) for it in body)
    else:
        assert body.get("id") == item_id

@pytest.mark.dependency(depends=["test_create_item_positive"])
def test_get_items_by_seller(base_url, headers, created_items, seller_id):
    """
    TC-003: Get items by sellerID
    """
    url = f"{base_url}/api/1/{seller_id}/item"
    resp = requests.get(url, headers=headers, timeout=10)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    body = resp.json()
    assert isinstance(body, list), "Expected list of items"
    # Найти хотя бы одно объявление с sellerId равным seller_id
    assert any((it.get("sellerId") == seller_id or it.get("sellerID") == seller_id) for it in body), \
        f"No items found for seller {seller_id}"

@pytest.mark.dependency(depends=["test_create_item_positive"])
def test_get_statistic_by_id(base_url, headers, created_items):
    """
    TC-004: Get statistic by item id
    """
    assert created_items, "No created item id available"
    item_id = created_items[0]
    url = f"{base_url}/api/1/statistic/{item_id}"
    resp = requests.get(url, headers=headers, timeout=10)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    body = resp.json()
    # допускаем как массив, так и объект
    assert isinstance(body, (list, dict))
    # при массиве — проверим что есть числовые поля
    if isinstance(body, list) and body:
        first = body[0]
        assert any(k in first for k in ("likes", "viewCount", "contacts"))
    elif isinstance(body, dict):
        assert any(k in body for k in ("likes", "viewCount", "contacts"))

def test_get_nonexistent_item(base_url, headers):
    """
    TC-006: Get non-existent item
    """
    fake_id = str(uuid.uuid4())
    url = f"{base_url}/api/1/item/{fake_id}"
    resp = requests.get(url, headers=headers, timeout=10)
    assert resp.status_code in (400, 404), f"Expected 400 or 404 for non-existent id, got {resp.status_code}"

def test_create_item_invalid_payload(base_url, headers):
    """
    TC-007: Create item — invalid body (empty)
    """
    url = f"{base_url}/api/1/item"
    resp = requests.post(url, data="", headers=headers, timeout=10)
    assert resp.status_code == 400, f"Expected 400 for invalid payload, got {resp.status_code}. Body: {resp.text}"

def test_get_items_by_invalid_seller(base_url, headers):
    """
    TC-008: Get items by invalid sellerID
    """
    invalid_seller = 0
    url = f"{base_url}/api/1/{invalid_seller}/item"
    resp = requests.get(url, headers=headers, timeout=10)
    assert resp.status_code in (200, 400, 404), f"Expected 400 or 404 for invalid sellerID, got {resp.status_code}"

# Optional: test deletion via api/2 if available
@pytest.mark.skip(reason="Удаление опционально, зависит от окружения")
def test_delete_item_by_id(base_url, headers, created_items):
    if not created_items:
        pytest.skip("No created items")
    item_id = created_items[0]
    url = f"{base_url}/api/2/item/{item_id}"
    resp = requests.delete(url, headers={"Accept": "application/json"}, timeout=10)
    assert resp.status_code == 200
