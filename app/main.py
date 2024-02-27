from flask import Flask, jsonify, request, render_template
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
mongo_client = MongoClient("mongodb+srv://svetozarevicmila21:XpQdxRAz8UO3TkXT@cluster0"
                           ".cgdrjnj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
mongo_collection = mongo_client.users_vouchers.vouchers

# Telegram bot token
TELEGRAM_BOT_TOKEN = '6922326558:AAHXCO05eruWBSJ08_cFBzk-v2_-KjBnsy8'
bot = Bot(token=TELEGRAM_BOT_TOKEN)


# Define the models for SQLAlchemy
class UserInfo(db.Model):
    __tablename__ = 'user_info'

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    spendings = db.relationship('UserSpending', backref='user')


class UserSpending(db.Model):
    __tablename__ = 'user_spending'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_info.user_id'), nullable=False)
    money_spent = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)


@app.route('/')
def index():
    return render_template('index.html')


# Route to get total spending for a user
@app.route('/total_spent/<int:user_id>', methods=['GET'])
def total_spent(user_id):
    total_spent = db.session.query(db.func.avg(UserSpending.money_spent)).filter_by(user_id=user_id).scalar()

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

    total_spending_by_age_range = {}

    for range_name, age_range in age_ranges.items():
        total_spending = db.session.query(db.func.sum(UserSpending.money_spent)).\
            join(UserInfo, UserInfo.user_id == UserSpending.user_id).\
            filter(UserInfo.age >= age_range[0], UserInfo.age <= age_range[1]).scalar() or 0
        total_spending_by_age_range[range_name] = total_spending

    asyncio.run(send_telegram_message(total_spending_by_age_range))
    return jsonify(total_spending_by_age_range), 200


# Mongodb
@app.route('/write_to_mongodb', methods=['POST'])
def write_to_mongodb():
        try:
            num_users = UserInfo.query.all()
            for user in num_users:
                total_spent = (db.session.query(db.func.sum(UserSpending.money_spent)).filter_by(user_id=user.user_id).scalar())
                if total_spent is not None and total_spent >=500:
                    user_data = {
                        'user_id': user.user_id,
                        'name': user.name,
                        'email': user.email,
                        'age': user.age
                    }
                    mongo_collection.insert_one(user_data)

            return jsonify({'message': 'Successfully added to MongoDB'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/save_user', methods=['POST'])
def save_user():
    if request.method == 'POST':
        first_name = request.form['firstName']
        email = request.form['email']
        age = request.form['age']
        spent_money = request.form['spentMoney']
        year = request.form['year']

        new_user = UserInfo(name=first_name, email=email, age=age)
        db.session.add(new_user)
        db.session.commit()

        user_id = new_user.user_id

        new_spending = UserSpending(user_id=user_id, money_spent=spent_money, year=year)
        db.session.add(new_spending)
        db.session.commit()

        return 'User saved successfully!'


@app.route('/send_telegram_message', methods=['POST'])
def send_telegram_message_route():
    try:
        total_spending_by_age_range = request.get_json()
        asyncio.run(send_telegram_message(total_spending_by_age_range))
        return jsonify({'message': 'Telegram message successfully sent'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


async def send_telegram_message(average_spending_by_age):
    chat_id = '6609218734'
    message = "Average Spending by Age Ranges:\n"
    for range_name, avg_spending in average_spending_by_age.items():
        message += f"{range_name}: ${avg_spending: .2f}\n"

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
        user = UserInfo.query.filter_by(name=user_info['name']).first()
        if not user:
            new_user = UserInfo(name=user_info['name'], email=user_info['email'], age=user_info['age'])
            db.session.add(new_user)
        else:
            user.email = user_info['email']
            user.age = user_info['age']

    db.session.commit()

    user_spending_info = {
        'Mila': {'money_spent': 2000, 'year': 2021},
        'Marija': {'money_spent': 6000, 'year': 2022},
        'Boko': {'money_spent': 4000, 'year': 2023}
    }

    for user_info in users_info:
        user_name = user_info['name']
        user = UserInfo.query.filter_by(name=user_name).first()
        if user:
            user_id = user.user_id
            if UserSpending.query.filter_by(user_id=user_id).count() == 0:
                spending_info = user_spending_info[user_name]
                sample_spending = UserSpending(user_id=user_id,
                                               money_spent=spending_info['money_spent'],
                                               year=spending_info['year'])
                db.session.add(sample_spending)

    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
