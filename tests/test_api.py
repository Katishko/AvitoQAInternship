import pytest
import requests
import uuid
import time


@pytest.mark.dependency()
def test_create_item_positive(base_url, headers, seller_id, created_items):
    """
    TC-001: Создание объявления с корректным телом запроса
    """
    url = f"{base_url}/api/1/item"

    payload = {
        "sellerID": seller_id,
        "name": f"test-item-{int(time.time())}",
        "price": 100,
        "statistics": {"likes": 1, "viewCount": 2, "contacts": 3}
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

    body = resp.json()
    assert "status" in body, "Missing 'status' field in response"

    # ожидаем строку вида "Сохранили объявление - <uuid>"
    parts = body["status"].split(" - ")
    assert len(parts) == 2, f"Unexpected status format: {body['status']}"

    item_id = parts[1].strip()

    # Проверка корректности uuid
    try:
        uuid.UUID(item_id)
    except ValueError:
        pytest.fail(f"Returned id is not valid UUID: {item_id}")

    created_items.append(item_id)


@pytest.mark.dependency(depends=["test_create_item_positive"])
def test_get_item_by_id(base_url, headers, created_items):
    """
    TC-002: Получение объявления по ID
    """
    item_id = created_items[0]
    url = f"{base_url}/api/1/item/{item_id}"

    resp = requests.get(url, headers=headers, timeout=10)
    assert resp.status_code == 200

    body = resp.json()

    # API может вернуть объект или массив из одного объекта
    if isinstance(body, list):
        assert any(obj.get("id") == item_id for obj in body), "Item not found in returned list"
    else:
        assert body.get("id") == item_id, f"Expected id={item_id}, got {body.get('id')}"


@pytest.mark.dependency(depends=["test_create_item_positive"])
def test_get_items_by_seller(base_url, headers, created_items, seller_id):
    """
    TC-003: Получение всех объявлений продавца
    """
    url = f"{base_url}/api/1/{seller_id}/item"
    resp = requests.get(url, headers=headers, timeout=10)
    assert resp.status_code == 200

    body = resp.json()
    assert isinstance(body, list), "Expected list of items"

    # хотя бы одно объявление должно принадлежать seller_id
    assert any(
        it.get("sellerId") == seller_id or it.get("sellerID") == seller_id
        for it in body
    ), f"No items found for seller {seller_id}"


@pytest.mark.dependency(depends=["test_create_item_positive"])
def test_get_statistic_by_id(base_url, headers, created_items):
    """
    TC-004: Получение статистики объявления по ID
    """
    item_id = created_items[0]
    url = f"{base_url}/api/1/statistic/{item_id}"

    resp = requests.get(url, headers=headers, timeout=10)
    assert resp.status_code == 200

    body = resp.json()
    assert isinstance(body, (dict, list)), "Unexpected response type"

    # Проверяем наличие ключей статистики
    expected_keys = {"likes", "viewCount", "contacts"}

    if isinstance(body, dict):
        assert expected_keys & body.keys(), "Statistic fields missing"
    elif isinstance(body, list) and body:
        assert expected_keys & body[0].keys(), "Statistic fields missing in list item"


def test_get_nonexistent_item(base_url, headers):
    """
    TC-006: Запрос объявления с несуществующим ID
    """
    fake_id = str(uuid.uuid4())
    url = f"{base_url}/api/1/item/{fake_id}"

    resp = requests.get(url, headers=headers, timeout=10)
    assert resp.status_code in (400, 404), f"Unexpected status code: {resp.status_code}"


def test_create_item_invalid_payload(base_url, headers):
    """
    TC-007: Создание объявления с пустым телом запроса
    """
    url = f"{base_url}/api/1/item"

    resp = requests.post(url, data="", headers=headers, timeout=10)
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"


def test_get_items_by_invalid_seller(base_url, headers):
    """
    TC-008: Получение объявлений по некорректному sellerID
    """
    invalid_seller = 0
    url = f"{base_url}/api/1/{invalid_seller}/item"

    resp = requests.get(url, headers=headers, timeout=10)
    assert resp.status_code in (200, 400, 404), f"Unexpected status code {resp.status_code}"


@pytest.mark.skip(reason="Удаление зависит от окружения")
def test_delete_item_by_id(base_url, headers, created_items):
    """
    TC-005: Удаление объявления
    """
    if not created_items:
        pytest.skip("No created items")

    item_id = created_items[0]
    url = f"{base_url}/api/2/item/{item_id}"

    resp = requests.delete(url, headers=headers, timeout=10)
    assert resp.status_code == 200































