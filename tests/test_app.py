import pytest
import app.app as appmod

@pytest.fixture(scope="module")
def client():
    app = appmod.app
    app.testing = True
    with app.test_client() as c:
        yield c

def test_health(client):
    rv = client.get('/health')
    assert rv.status_code == 200
    assert rv.get_json()['status'] == 'ok'

def test_user_default(client):
    rv = client.get('/user')
    assert rv.status_code == 200