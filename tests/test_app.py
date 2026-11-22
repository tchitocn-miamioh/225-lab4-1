
import pytest
import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_database = tmp_path / "test_contacts.db"

    monkeypatch.setattr(
        main,
        "DATABASE",
        str(test_database)
    )

    main.app.config["TESTING"] = True
    main.init_db()

    with main.app.test_client() as client:
        yield client


def test_homepage_loads(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Add Contact" in response.data


def test_add_contact(client):
    response = client.post("/", data={
        "name": "John Smith",
        "phone": "6145550101"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"John Smith" in response.data
    assert b"Contact added successfully" in response.data


def test_invalid_phone_rejected(client):
    response = client.post("/", data={
        "name": "Mary Johnson",
        "phone": "invalid-phone"
    }, follow_redirects=True)

    assert b"Invalid phone number" in response.data
    assert b"Mary Johnson" not in response.data


def test_missing_name_rejected(client):
    response = client.post("/", data={
        "name": "",
        "phone": "6145550102"
    }, follow_redirects=True)

    assert b"Invalid name" in response.data


def test_delete_contact(client):
    client.post("/", data={
        "name": "David Brown",
        "phone": "6145550103"
    })

    response = client.post("/", data={
        "action": "delete",
        "contact_id": "1"
    }, follow_redirects=True)

    assert b"Contact deleted successfully" in response.data
    assert b"David Brown" not in response.data


def test_sql_injection_does_not_delete_table(client):
    malicious_name = "Robert'); DROP TABLE contacts; --"

    client.post("/", data={
        "name": malicious_name,
        "phone": "6145550104"
    })

    db = main.get_db()
    try:
        result = db.execute(
            "SELECT COUNT(*) FROM contacts"
        ).fetchone()

        assert result[0] == 1
    finally:
        db.close()


def test_security_headers(client):
    response = client.get("/")

    assert response.headers["X-Frame-Options"] == "DENY"

    assert response.headers[
        "X-Content-Type-Options"
    ] == "nosniff"

    assert "Content-Security-Policy" in response.headers
