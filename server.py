from main import app, db
from main.models import User, BankLoan, UserLoan, Subscription, Transaction, Contact

from functools import wraps
from flask import jsonify

import datetime

import os, sys, json, random, base64, time
from flask import Flask, send_file, request
from flask_cors import CORS

import pyttsx3
import whisper
from transformers import pipeline

from s_graph import Graph

classifier = pipeline("zero-shot-classification",
                    model="valhalla/distilbart-mnli-12-1")


whisper_model = whisper.load_model("base")

#voice engine setup
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('rate',180)
engine.setProperty('voice',voices[1].id)

sgraph = Graph(classifier)


def process_whisper(filename):
    # load audio and pad/trim it to fit 30 seconds
    audio = whisper.load_audio(filename)
    audio = whisper.pad_or_trim(audio)

    # make log-Mel spectrogram and move to the same device as the model
    mel = whisper.log_mel_spectrogram(audio).to(whisper_model.device)

    # detect the spoken language
    # _, probs = whisper_model.detect_language(mel)
    # print(f"Detected language: {max(probs, key=probs.get)}")

    # decode the audio
    options = whisper.DecodingOptions()
    result = whisper.decode(whisper_model, mel, options)

    return result.text

def process_zero_shot(text, labels):
    out = classifier(text, labels)
    print(out)
    return out["labels"][0], out


def tts(text):
    fname = f"{random.randrange(0,10000)}_out.mp3"

    # say method on the engine that passing input text to be spoken
    engine.save_to_file(text, fname)
    engine.runAndWait()

    binary_audio  = None
    with open(fname, "rb") as f:
       binary_audio = f.read()

    os.remove(fname)
    return base64.b64encode(binary_audio).decode("utf-8")


def extract_json(func):
    @wraps(func)

    def wrapper(*args, **kwargs):
        if (content_type == 'application/json'):
            data = request.get_json()
            return func(data, *args, **kwargs)
        else:
            return jsonify({'error': 'Content-Type not supported!' })

    return wrapper


def compute_max_loan(user):
    #otigers shit here
    return user.balance ** 2 / 2


@app.route('/users', methods=['POST'])
@extract_json
def create_user(data):
    user = User(username=data['username'], email=data['email'], password=data['password'], 
        phone_number= data["phone_number"], 
        firstname= data["firstname"], surname= data["surname"])
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'})


@app.route('/users/get_balance', methods=['GET'])
@extract_json
def get_user_balance(data):
    user = User.query.get(id=data["user_id"])
    return jsonify({'balance': user.balance})


@app.route('/users', methods=['GET'])
@extract_json
def get_user(data):
    user = User.query.get(id=data["user_id"])
    return jsonify(user)


@app.route('/users/', methods=['PUT'])
@extract_json
def update_user(data):
    user = User.query.get(data["user_id"])
    user.username = data['username']
    user.email = data['email']
    user.phone_number = data['phone_number']
    user.firstname = data['firstname']
    user.surname = data['surname']
    db.session.commit()
    return jsonify({'message': 'User updated successfully'})

@app.route('/users/', methods=['DELETE'])
@extract_json
def delete_user(data):
    user = User.query.get(data["user_id"])
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'})
    else:
        return jsonify({'error': 'User could not be found'})

@app.route('/users/<int:user_id>/get_bank_loans', methods=['GET'])
def get_user_loans(user_id):
    loans = BankLoan.query.all(user_id=user_id)
    print(loans)
    return jsonify(loans) #not sure about this

@app.route('/bank_loans', methods=['POST'])
@extract_json
def create_bank_loan(data):
    user = User.query.get(data['user_id'])
    if user:
        if data['amount'] <= compute_max_loan(user):
            loan = BankLoan(user=user, amount=data['amount'], interest_rate=data['interest_rate'])
            user.balance += loan.amount #there obv needs to be other mechanisms tô track the loan repayment
            db.session.add(loan)
            db.session.commit()
            return jsonify({'message': 'Loan created successfully'})
        else:
            return jsonify({'error': 'You do not qualify for this loan amount.'})


@app.route('/bank_loans/repay/', methods=['POST'])
@extract_json
def repay_bank_loan(data):
    loan = BankLoan.query.get(data["loan_id"])
    user = User.query.get(loan.user_id)
    if loan and user:
        amount_owed = loan.amount * interest_rate * ((datetime.datetime.now() - loan.start_date).days / 365)
        if user.balance >= amount_owed:
            user.balance -= loan.amount #very rudimentary
            loan.active = False 
            loan.end_date = datetime.datetime.now()
            db.session.commit()
            return jsonify({'message': 'Loan repaid successfully'})
        else:
            return jsonify({'message': 'Loan could not be repaid. Insufficient funds!'})
    else:
        return jsonify({'error': 'Loan or User could not be found.'})



@app.route('/bank_loans', methods=['DELETE'])
@extract_json
def revert_bank_loan(datra):
    loan = BankLoan.query.get(data["loan_id"])
    user = User.query.get(loan.user_id)
    if loan and user:
        user.balance -= loan.amount #very rudimentary
        db.session.delete(loan)
        db.session.commit()
        return jsonify({'message': 'Loan deleted successfully'})
    else:
        return jsonify({'error': 'Loan or User could not be found.'})




@app.route('/subscriptions/create', methods=['POST'])
@extract_json
def create_subscription(data):
    user = User.query.get(data['user_id'])
    subscription = Subscription(creator=user_id, name=data['name'], 
            amount=data['amount'], interval=data['interval'], 
            action=data['action'])
    db.session.add(subscription)
    db.session.commit()
    return jsonify({'message': 'Subscription created successfully'})

@app.route('/subscriptions/subscribe/', methods=['POST'])
@extract_json
def join_subscription(data, subscription_id):
    user = User.query.get(data['user_id'])
    subscription = Subscription.query.get(id=data['subscription_id'])

    #some many to many shit to happen here

    db.session.commit()
    return jsonify({'message': 'Subscription addded successfully'})

@app.route('/subscriptions/', methods=['PUT'])
@extract_json
def update_subscription(data):
    subscription = Subscription.query.get(data['subscription_id'])
    if data["owner_id"] == subscription.creator_id:
        #maybe needs more nuance?
        subscription.name = data['name']
        subscription.amount = data['amount']
        subscription.interval = data['interval']
        subscription.end_date = data['end_date']
        subscription.action = data['action']
        db.session.commit()
        return jsonify({'message': 'Subscription updated successfully'})
    else:
        return jsonify({'error': 'Only the owner can edit the subscription.'})

@app.route('/subscriptions/', methods=['DELETE'])
@extract_json
def delete_subscription():
    subscription = Subscription.query.get(data['subscription_id'])
    db.session.delete(subscription)
    db.session.commit()
    return jsonify({'message': 'Subscription deleted successfully'})



@app.route('/contacts/upload', methods=['POST'])
@extract_json
def create_contact(data):
    user = User.query.get(data['user_id'])
    phone_numbers = data['phone_numbers']
    for number in  phone_numbers:
        corresponding_user = User.query.get(phone_number = number)
        if corresponding_user:
            #create new contact
            contact = Contact(luser_id=user.id, ruser_id= corresponding_user.id, phone_number=data['phone_number'] )
            db.session.add(contact)
            db.session.commit()
   
    return jsonify({'message': 'Contacts created successfully'})


@app.route('/contacts', methods=['GET'])
@extract_json
def get_contacts(data):
    contacts = Contact.query.all(luser_id= data["user_id"] )
    return jsonify(contacts)


@app.route('/contacts', methods=['DELETE'])
@extract_json
def delete_contact(data):
    contact = Contact.query.get(data["contact_id"])
    if contact:
        db.session.delete(contact)
        db.session.commit()
        return jsonify({'message': 'Contact deleted successfully'})
    else:
        return jsonify({'error': 'Contact could not be found'})



@app.route('/transactions', methods=['POST'])
@extract_json
def create_transaction(data):
    sender = User.query.get(data['user_id'])
    receiver = User.query.get(data['user_id'])
    if user.balance >= data['amount'] and sender and receiver:
        transaction = Transaction(sender_id = data['sender_id'], receiver_id= data['receiver_id'], amount=data['amount'], description=data['description'], category=data['category'])
        sender.balance -= transaction.amount
        receiver.balance += transaction.amount
        db.session.add(transaction)
        db.session.add(sender)
        db.session.add(receiver)
        db.session.commit()
    else:
        return jsonify({"error": "insufficient funds"})
    return jsonify({'message': 'Transaction created successfully'})

@app.route('/transactions/all', methods=['GET'])
@extract_json
def get_transactions(data):
    user = User.query.all(data['user_id'])
    if user:
        transactions = Transaction.query.all(sender_id = data["user_id"])
        return jsonify(transactions)
    return jsonify({'error': 'User could not be found.'})





@app.route('/transactions', methods=['DELETE'])
@extract_json
def revert_transaction(data):
    transaction = Transaction.query.get(data['transaction_id'])
    if transaction:
        sender = User.query.get(transaction.sender_id)
        receiver = User.query.get(transaction.receiver_id)
        if sender and receiver:
            sender.balance += transaction.amount
            receiever.balance -= transaction.amount
            db.session.delete(transaction)
            db.session.add(sender)
            db.session.add(receiver)
            db.session.commit()
            return jsonify({'message': 'Transaction deleted successfully'})
        return jsonify({"error": "Sender or Receiver does not exist."})
    else:
        return jsonify({"error": "Transaction does not exist."})

@app.route('/ai_chat', methods=['DELETE'])
@extract_json
def ai_chat(data):
    fname = f"{random.randrange(0,10000)}_in.mp3"
    with open(fname, "wb") as f:
        f.write(base64.b64decode(_json["audio"]))

    #meta should include user_id

    text = process_whisper(fname)
    os.remove(fname)
    history = data["history"]
    state  = data["state"]
    meta = data["meta"]
    history, next_state, text_output, meta = s_graph.exec_state(history, text, state, meta)
    binary_audio = tts(response)

    return jsonify({"text" : text_output, "audio_raw" : binary_audio,
 "history": history, "next_state": next_state, "meta": meta})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

