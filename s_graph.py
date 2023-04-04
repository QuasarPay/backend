import requests

SERVER_URL  = "http://localhost:5000"


def get_acc_balance(id):
    #interface this with BE
    # response = requests.get(f"{SERVER_URL}/users/get_balance", json={"user_id": id})
    # return response.json()["balance"]

    return 200000

####################################

def generic_text_map_response(history, text, classifier, next_map, meta):
    probs = classifier(text, list(next_map.keys()))
    print(probs)

    nstate = probs["labels"][0]
    _nstate = next_map[nstate][1]
    text_output = next_map[nstate][0]
    history.append(text_output)

    print(probs)

    return history, _nstate, text_output, meta


def balance_func(history, text, classifier, next_map, meta):
    probs = classifier(text, list(next_map.keys()))
    chosen = probs["labels"][0]

    nstate = next_map[chosen][1]
    text_output = next_map[chosen][0]


    if chosen == "continue" or chosen == "yes":
        text_output = f"Your account balance is {get_acc_balance(2)}. "
   
    history.append(text_output)

    return history, nstate, text_output, meta


def amount_to_transfer(history, text, classifier, next_map, meta):
    probs = classifier(text, list(next_map.keys()))
    chosen = probs["labels"][0]
    
    nstate = next_map[chosen][1]
    text_output = next_map[chosen][0]


    amount = 5000
    # if text_output == None:
    #     words = text.split(" ")
    #     for word in words:
    #         word = word.replace(",", " ")
    #         if word.isnumeric():
    #             amount = int(word)
    #             meta["amount"] = amount

    #             break

    text_output = f"You have chosen to transfer {amount} naira. Continue?"
   
    # if amount == None:
    # nstate = "confirm transfer"
    # text_output = ""
    
    # if amount > get_acc_balance(meta["user_id"]):
    #     nstate = "amount to transfer"
    #     text_output = "You do not have enough money for this transfer."

    history.append(text_output)

    print(probs)

    return history, nstate, text_output, meta


def account_details(history, text, classifier, next_map, meta):

    probs = classifier(text, list(next_map.keys()))
    chosen = probs["labels"][0]
    
    nstate = next_map[chosen][1]
    text_output = next_map[chosen][0]



    account_no = 2002
    # if text_output == None:
    #     words = text.split("")
    #     for word in words:
    #         word = word.replace(",", "")
    #         if word.isnumeric():
    #             account_no = word
    #             meta["account_no"] = int(word)
    #             break

    text_output = f"You have chosen to transfer to this account: {account_no} . Continue?"

    nstate = "amount to transfer"
   
    # if account_no == None:
    #     nstate = "account details"
    #     text_output = "Did not hear account to be transferred to. Please try again."
    
    history.append(text_output)

    print(probs)

    return history, nstate, text_output, meta

   
HELP_TEXT = "Hello there!  I am your AI assistant ...."
BACK_TEXT = "You have chosen to go back."

#previous state rn seems entirely descriptive but not part of the function. Maybe it
#would matter if we were building a graph
graph_data = {
    "hello": {
        "prev" :[],
        "func" : generic_text_map_response,
        "next" :{"balance": ["You have chosen to check your account balance. Continue? ", "balance"] , 
                 "transfer": ["You have chosen to transfer money. Continue?", "transfer"], 
                 "loan": ["You have selected loan. Continue?", "loan" ], 
                 "back": [HELP_TEXT, "hello"], 
                #  "help": [HELP_TEXT, "hello"]
                 }
    },
    "balance": {
        "prev" :["hello"],
        "func" : balance_func,
        "next" :{"continue": [None, "hello"] , #if None, we have to generate the text
                 "yes": [None, "hello"] , 
                 "no": [BACK_TEXT, "hello"], 
                 "back": [BACK_TEXT, "hello"], 
                #  "help": [HELP_TEXT, "balance"]
                }
    },
    "transfer": {
        "prev" :["hello"],
        "func" : generic_text_map_response ,
        # "next" :["account details", "back", "help"]
        "next" :{"continue": ["Please tell us the account number and bank of the person you wish to transfer to.", 
                    "account details", "account details"] , 
                 "yes": ["Please tell us the account number and bank of the person you wish to transfer to.", 
                    "account details", "account details"] , 
                 "no": [BACK_TEXT, "hello"], 
                 "back": [BACK_TEXT, "hello"], 
                #  "help": [HELP_TEXT, "hello"]
                }
    },
    "account details": {
        "prev" :["transfer"],
        "func" : account_details,
        "next" :{"amount to transfer": [None, "amount to transfer"], 
                 "back": ["You have chosen to go back and say the account number again", "transfer"], 
                #  "help": [HELP_TEXT, "account details"]
                }
    },
    "amount to transfer": {
        "prev" :["account details"],
        "func" : amount_to_transfer,
        "next" :{"amount to transfer": [None, "confirm transfer"], 
                #  "back": ["You have chosen to go back and say the account number again", "account details"], 
                #  "help": [HELP_TEXT, "help"]
                }
    },
    "confirm transfer": {
        "prev" :["amount to transfer"],
        "func" : generic_text_map_response,
        "next" :{"yes": ["Transfer was completed!", "hello"], 
                 "back": ["You have chosen to go back and say the amount again", "transfer"], 
                #  "help": [HELP_TEXT, "help"]
                }
    },
    # "help": {
    #     "prev" :["Everythhing"],
    #     "func" : generic_text_map_response, 
    #     "next" :{"hello" : ["This is the help menu...", "hello"]} #how do we track and revert?
    # },

    # "done": {
    #     "prev" :["Everythhing"],
    #     "func" : generic_text_map_response, 
    #     "next" :{"done" : ["Thank you for banking with us!", "done"]} #how do we track and revert?
    # },

    # "loan": {
    #     "prev" :["hello"],
    #     "func" : loan, 
    #     "next" :["social loan", "traditional loan", "back", "help"]
    # },
    # "social loan": {
    #     "prev" :["hello"],
    #     "func" : social_loan ,
    #     "next" :["choose person", "back", "help"]
    # },
    # "choose person": {
    #     "prev" :["social loan"],
    #     "func" : choose_person_func,
    #     "next" :["person name", "back", "reset", "help"]
    # },
    # "person name": {
    #     "prev" :["social loan"],
    #     "func" : person_name_func #read out persons settings 
    #     "next" :["set amount", "back", "reset", "help"]
    # },
    # "set amount": {
    #     "prev" :["traditional loan", "person name"],
    #     "func" : set_loan_amount,
    #     "next" :["confirm loan", "back", "reset", "help"]
    # },
    # "confirm loan": {
    #     "prev" :["amount"],
    #     "func" : confirm_loan
    #     "next" :["done", "back", "reset", "help"]
    # },
    # "traditional loan": {
    #     "prev" :["hello"],
    #     "func" : traditional_loan,
    #     "next" :["set amount", "back", "reset", "help"]
    # },
}



class Graph:
    def __init__(self, classifier ):
        #build graph from data
        self.data = graph_data
        self.classifier = classifier

    def exec_state(self, history, text, meta, classifier):
        
        if not "state" in meta.keys():
            meta["state"] = "hello"

        sinfo = self.data[meta["state"]]
        history, next_state, text_output, meta = sinfo["func"](history, text, classifier, sinfo["next"], meta)

        return history, next_state, text_output, meta