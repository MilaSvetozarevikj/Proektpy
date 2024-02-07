from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from pymongo import MongoClient

app = Flask(__name__)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configure MongoDB
mongo_client = MongoClient('mongodb://localhost:27017')
mongo_db = mongo_client['users_vouchers']
mongo_collection = mongo_db['vouchers']

# SQLAlchemy Model
class UserInfo(db.Model):
    __tablename__ = 'user_info'

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    spendings = db.relationship('UserSpending', backref='user', lazy=True)

    def __repr__(self):
        return f"<UserInfo(user_id={self.user_id}, name={self.name}, email={self.email}, age={self.age})>"

class UserSpending(db.Model):
    __tablename__ = 'user_spending'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_info.user_id'), nullable=False)
    money_spent = db.Column(db.Float, nullable=False)
    year = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<UserSpending(user_id={self.user_id}, money_spent={self.money_spent}, year={self.year})>"

# API Endpoint 1: Retrieve Total Spending by User
@app.route('/total_spent/<int:user_id>', methods=['GET'])
def total_spent(user_id):
    total_spent = UserSpending.query.filter_by(user_id=user_id).with_entities(
        db.func.sum(UserSpending.money_spent)).scalar()

    if total_spent is not None:
        response = {'user_id': user_id, 'total_spent': float(total_spent)}
        return jsonify(response), 200
    else:
        return jsonify({'error': 'User not found'}), 404

# API Endpoint 2: Calculate Average Spending by Age Ranges
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

    # for range_name, age_range in age_ranges.items():
    #     average_spending = UserSpending.query.filter(UserSpending.age >= age_range[0],
    #                                                  UserSpending.age <= age_range[1]).with_entities(
    #         db.func.avg(UserSpending.money_spent)).scalar()
    #     average_spending_by_age[range_name] = float(average_spending) if average_spending is not None else 0.0

    return jsonify(average_spending_by_age), 200

# API Endpoint 3: Write user data to MongoDB
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

        # Create the tables in the SQL database
with app.app_context():
    db.create_all()

    sample_user = UserInfo(name='Marija', email='marija25@gmail.com', age=25)
    db.session.add(sample_user)
    db.session.commit()

    sample_spending = UserSpending(user_id=sample_user.user_id, money_spent=1000, year=2023)

    db.session.add(sample_spending)
    db.session.commit()

if __name__ == '__main__':


    app.run(debug=True)