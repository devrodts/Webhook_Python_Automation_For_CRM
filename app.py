from flask import Flask, request, jsonify
import requests
import os
from rdstation.main import RDStation


from dotenv import load_dotenv
load_dotenv()


token = os.getenv("RD_TOKEN")
rds = RDStation(token)


app = Flask(__name__)

app.route("/webhook", methods=["GET", "POST"])



def webhook():
    if request.method == "GET":
        contacts = rds.CRM().contacts().lists()
        print(contacts)
        return
    

    elif request.method == "POST":
        

        return
    




def criar_contato():
    return