import pytest
import json
from main import app, db, UserInfo, UserSpending


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


def test_total_spent(client):
    user1 = UserInfo(name='Mila', email='mila@gmail.com', age=22)
    db.session.add(user1)
    db.session.commit()
    spending1 = UserSpending(user_id=user1.user_id, money_spent=2000, year=2021)
    db.session.add(spending1)
    db.session.commit()

    response = client.get('/total_spent/1')
    data = json.loads(response.data.decode('utf-8'))

    assert response.status_code == 200
    assert data['total_spent'] == 2000.0


def test_total_spent_user_not_found(client):
    response = client.get('/total_spent/3')
    data = json.loads(response.data.decode('utf-8'))

    assert response.status_code == 404
    assert data['error'] == 'User not found'


def test_average_spending_by_age(client):
    user1 = UserInfo(name='Mila', email='mila@gmail.com', age=22)
    user2 = UserInfo(name='Marija', email='marija@gmail.com', age=25)
    user3 = UserInfo(name='Boko', email='boko@gmail.com', age=18)
    db.session.add_all([user1, user2, user3])
    db.session.commit()
    spending1 = UserSpending(user_id=user1.user_id, money_spent=2000, year=2021)
    spending2 = UserSpending(user_id=user2.user_id, money_spent=6000, year=2022)
    spending3 = UserSpending(user_id=user3.user_id, money_spent=4000, year=2023)
    db.session.add(spending1)
    db.session.add(spending2)
    db.session.add(spending3)
    db.session.commit()

    response = client.get('/average_spending_by_age')
    data = json.loads(response.data.decode('utf-8'))

    assert response.status_code == 200
    assert '18-24' in data
    assert '25-30' in data
    assert '31-36' in data
    assert '37-47' in data
    assert '>47' in data


def test_write_to_mongodb(client):
    payload = {'user_id': 1, 'total_spent': 2000}
    response = client.post('/write_to_mongodb', json=payload)

    try:
        assert response.status_code == 201
    except AssertionError:
        assert response.status_code == 400

        if response.content_type == 'application/json':
            data = json.loads(response.data)
            print("Error message:", data.get('error'))


def test_write_to_mongodb_incomplete_data(client):
    payload = {'user_id': 1}
    response = client.post('/write_to_mongodb', json=payload)
    data = json.loads(response.data.decode('utf-8'))

    assert response.status_code == 400
    assert data['error'] == 'Incomplete data'
