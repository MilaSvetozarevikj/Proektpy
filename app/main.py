from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from pymongo import MongoClient
from telegram import Bot
import asyncio

app = Flask(__name__)

# Configuration for SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configuration for MongoDB
mongo_client = MongoClient("mongodb://localhost:27017")
mongo_db = mongo_client["users_vouchers"]
mongo_collection = mongo_db["vouchers"]

# Telegram bot token
TELEGRAM_BOT_TOKEN = '6922326558:AAHXCO05eruWBSJ08_cFBzk-v2_-KjBnsy8'
bot = Bot(token=TELEGRAM_BOT_TOKEN)


# Define the models for SQLAlchemy
class UserInfo(db.Model):
    __tablename__ = 'user_info'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    spendings = db.relationship('UserSpending', backref='user')

    def __repr__(self):
        return f"<UserInfo(user_id={self.user_id}, name={self.name}, email={self.email}, age={self.age})>"


class UserSpending(db.Model):
    __tablename__ = 'user_spending'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_info.user_id'), nullable=False)
    money_spent = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<UserSpending(user_id={self.user_id}, money_spent={self.money_spent}, year={self.year})>"


# Route to get total spending for a user
@app.route('/total_spent/<int:user_id>', methods=['GET'])
def total_spent(user_id):
    total_spent = (UserSpending.query.filter_by(user_id=user_id)
                   .with_entities(db.func.avg(UserSpending.money_spent)).scalar())

    if total_spent is not None:
        response = {'user_id': user_id, 'total_spent': float(total_spent)}
        return jsonify(response), 200
    else:
        return jsonify({'error': 'User not found'}), 404


# Route to get average spending by age
@app.route('/average_spending_by_age', methods=['GET'])
def average_spending_by_age():
    age_ranges = {
        '18-24': (18, 24),
        '25-30': (25, 30),
        '31-36': (31, 36),
        '37-47': (37, 47),
        '>47': (48, 150)
    }

    average_spending_by_age = {}

    for range_name, age_range in age_ranges.items():
        average_spending = db.session.query(db.func.avg(UserSpending.money_spent)). \
            join(UserInfo).filter(UserInfo.age >= age_range[0],
                                  UserInfo.age <= age_range[1]).scalar()
        average_spending_by_age[range_name] = float(average_spending) if average_spending is not None else 0.0

    asyncio.run(send_telegram_message(average_spending_by_age))

    return jsonify(average_spending_by_age), 200


#Mongodb
@app.route('/write_to_mongodb', methods=['POST'])
def write_to_mongodb():
    try:
        data = request.get_json()

        if 'user_id' not in data or 'total_spent' not in data:
            return jsonify({'error': 'Incomplete data'}), 400

        mongo_collection.insert_one(data)

        return jsonify({'message': 'Successfully added to MongoDB'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Function to send statistics to Telegram bot
async def send_telegram_message(average_spending_by_age):
    chat_id = '6609218734'
    message = "Average Spending by Age Ranges:\n"
    for range_name, avg_spending in average_spending_by_age.items():
        message += f"{range_name}: ${avg_spending:.2f}\n"

    await bot.send_message(chat_id=chat_id, text=message)


# Initialize database tables
with app.app_context():
    db.create_all()

    # Sample data
    users_info = [
        {'name': 'Mila', 'email': 'mila@gmail.com', 'age': 22},
        {'name': 'Marija', 'email': 'marija@yahoo.com', 'age': 25},
        {'name': 'Boko', 'email': 'boko@gmail.com', 'age': 18}
    ]

    for user_info in users_info:
        new_user = UserInfo(name=user_info['name'], email=user_info['email'], age=user_info['age'])
        db.session.add(new_user)

    db.session.commit()

    user_spending_info = {
        'Mila': {'money_spent': 2000, 'year': 2021},
        'Marija': {'money_spent': 3000, 'year': 2022},
        'Boko': {'money_spent': 4000, 'year': 2023}
    }

    for user_info in users_info:
        user_name = user_info['name']
        user_id = UserInfo.query.filter_by(name=user_name).first().user_id
        spending_info = user_spending_info[user_name]

        sample_spending = UserSpending(user_id=user_id,
                                       money_spent=spending_info['money_spent'],
                                       year=spending_info['year'])
        db.session.add(sample_spending)

    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)