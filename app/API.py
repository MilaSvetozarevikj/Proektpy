import requests

FLASK_API_BASE_URL = 'http://localhost:5000'

def get_total_spent(user_id):
    url = f'{FLASK_API_BASE_URL}/total_spent/{user_id}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def write_to_mongodb(user_id, total_spent):
    if total_spent > 1000:
        url = f'{FLASK_API_BASE_URL}/write_to_mongodb'
        data = {'user_id': user_id, 'total_spent': total_spent}
        response = requests.post(url, json=data)
        if response.status_code == 201:
            print("Successfully written in MongoDB")
        else:
            print("Error.")

def get_average_spending_by_age():
    url = f'{FLASK_API_BASE_URL}/average_spending_by_age'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

if __name__ == '__main__':
    user_id = 1
    total_spent_data = get_total_spent(user_id)
    if total_spent_data:
        print("Total spend:", total_spent_data)

        if 'total_spent' in total_spent_data and total_spent_data['total_spent'] > 1000:
            write_to_mongodb(total_spent_data['user_id'], total_spent_data['total_spent'])

    average_spending_data = get_average_spending_by_age()
    if average_spending_data:
        print("Average spending by age:", average_spending_data)