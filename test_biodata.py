import pytest

def test_example():
    import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200


def test_login_page_loads(client):
    response = client.get("/login")
    assert response.status_code == 200


def test_invalid_login(client):
    response = client.post("/login", data={
        "username": "wrong",
        "password": "wrong"
    })
    assert b"Invalid credentials" in response.data


def test_admin_requires_login(client):
    response = client.get("/admin")
    assert response.status_code == 302  # redirected to login


def test_login_and_access_admin(client):
    # login first
    client.post("/login", data={
        "username": "admin",
        "password": "admin123"
    })

    response = client.get("/admin")
    assert response.status_code == 200
    assert True

import io
from PIL import Image

def test_form_submission(client):
    # Create a real in-memory image
    img = Image.new("RGB", (100, 100), color="red")
    img_io = io.BytesIO()
    img.save(img_io, format="JPEG")
    img_io.seek(0)

    data = {
        "name": "Test User",
        "age": "30",
        "sex": "Male",
        "occupation": "Engineer",
        "photo": (img_io, "test.jpg")
    }

    response = client.post(
        "/submit",
        data=data,
        content_type="multipart/form-data"
    )

    assert response.status_code == 200