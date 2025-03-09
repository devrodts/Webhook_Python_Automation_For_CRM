from flask import Flask, request, jsonify
import os
import json
from rdstation.main import RDStation
from flask_cors import CORS
import redis
from datetime import datetime, timedelta
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
CORS(app)
redis_client = redis.Redis(host='redis', port=6379, db=2)

RD_TOKEN = os.environ.get('RD_TOKEN')

handler = RotatingFileHandler('lead_distribution.log', maxBytes=5*1024*1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

TEAMS = [
    ["Consult 1", "Consult 2", "Consult 3", "Consult 4", "Consult 5", "Consult 6", "Consult 7", "Consult 8", "Consult 9"],
    ["Consult 10", "Consult 11", "Consult 12", "Consult 13", "Consult 14", "Consult 15", "Consult 16", "Consult 17", "Consult 18"],
    ["Consult 19", "Consult 20", "Consult 21", "Consult 22", "Consult 23", "Consult 24", "Consult 25", "Consult 26", "Consult 27"],
    ["Consult 28", "Consult 29", "Consult 30", "Consult 31", "Consult 32", "Consult 33", "Consult 34", "Consult 35", "Consult 36"],
    ["Consult 37", "Consult 38", "Consult 39", "Consult 40", "Consult 41", "Consult 42", "Consult 43", "Consult 44", "Consult 45"]
]

CONSULTANTS = {
    "Consult 1": "67462f65420831001d1a8d5a",
    "Consult 2": "6746330ed8e084001380bd24",
    "Consult 3": "6747226184402f00138485e4",
    "Consult 4": "66eae26c073c4b00187c6a83",
    "Consult 5": "67463ae37509ce001348ae33",
    "Consult 6": "674709be6dcd80001850b017",
    "Consult 7": "67116551199aa1001fb84de4",
    "Consult 8": "674df289acc8b10013d2b090",
    "Consult 9": "674df920a937e60013fc81b5",

    "Consult 10": "66eae3d177a330001bda997b",
    "Consult 11": "67472d8bd36ea600227ed955",
    "Consult 12": "66eae1def03bc80013485f04",
    "Consult 13": "674761ca6dcd80001351285d",
    "Consult 14": "674df923f527260013bfb952",
    "Consult 15": "674df0c65acffd0013c26e61",
    "Consult 16": "674def9a385afe0013922d91",

    "Consult 17": "67477de410f33a001a46dc19",
    "Consult 18": "66eae678f11e5a0017e8f6be",
    "Consult 19": "67486239f3a0b2001956fbb5",
    "Consult 20": "674783e250924800253a453b",
    "Consult 21": "67478ec63bf15c001ae24148",
    "Consult 22": "67478a871144f10015c3d1f8",
    "Consult 23": "674dfc024f9ae70013becb16",

    "Consult 24": "670526bce837f60014b8c099",
    "Consult 25": "66eae14abb5ac90013b7a478",

    "Consult 26": "66ec3633d234f5001a2b6147",
    "Consult 27": "66eb0569cb52cd001318caa0",
    "Consult 28": "67041029bd734e00267b6918",
    "Consult 29": "66ec12acef14bd00132d76a0",
    "Consult 30": "66ec643bf13cce0013ac1249",
    "Consult 31": "66f3fc2cca471f001a8b15b6"
}


ALL_CONSULTANTS = [c for team in TEAMS for c in team]


def reset_daily_counters():
    with redis_client.pipeline() as pipe:
        pipe.set('total_leads', 0)
        pipe.set('current_team_index', 0)
        for team_index, team in enumerate(TEAMS):
            pipe.set(f'team_current_index:{team_index}', 0)
            for consultant in team:
                pipe.set(f'consultant_count:{consultant}', 0)
        ttl = 259200  
        keys = (['total_leads', 'current_team_index']
                + [f'team_current_index:{i}' for i in range(len(TEAMS))]
                + [f'consultant_count:{c}' for c in CONSULTANTS.keys()])
        for key in keys:
            pipe.expire(key, ttl)
        pipe.execute()
    logging.info("Contadores reiniciados com TTL de 72 horas.")


def get_user_id_for_lead(lead_index):
    user_id = redis_client.get(f'lead:{lead_index}:user_id')
    return user_id

def get_next_consultant():
    total_leads = int(redis_client.get('total_leads') or 0)

    if total_leads <= 0:
        return None, None
    consultant_index = total_leads % len(ALL_CONSULTANTS)
    consultant_name = ALL_CONSULTANTS[consultant_index]
    
    user_id = CONSULTANTS.get(consultant_name)

    redis_client.incr(f'consultant_count:{consultant_name}')
    
    return consultant_name, user_id

@app.route("/webhook", methods=["POST"])
def webhook():

    if request.is_json:
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")
        phones = data.get("phone")

        horario_contato = data.get("horario_contato")
        valor_investimento = data.get("valor_investimento")
        preferencia_contato = data.get("preferencia_contato")

        if not all([name, email]):
            logging.error("Nome e e-mail são obrigatórios.")
            return jsonify({"Error": "Nome e e-mail são obrigatórios"}), 400

        phones = phones if isinstance(phones, list) else [phones]
        phone_payload = [{"phone": phone, "type": "cellphone"} for phone in phones]

        lead_id = f"{email}:{name}"

        if redis_client.exists(f"processed_leads:{lead_id}"):
            logging.info(f"Lead duplicado recebido e ignorado: {lead_id}")
            return jsonify({"message": "Lead já processado."}), 200

        redis_client.set(f"processed_leads:{lead_id}", 1, ex=259200)
        rds = RDStation(RD_TOKEN)

        if valor_investimento:
            contact_payload = {
                "name": f"{name} | {valor_investimento} | {horario_contato} | {preferencia_contato}",
                "emails": [{"email": email}],
                "phones": phone_payload,
            }
        else:
            contact_payload = {
                "name": name,
                "emails": [{"email": email}],
                "phones": phone_payload,
            }

        logging.info(f"Lead recebido: Nome={name}, Email={email}, Telefones={phones}")

        lock_acquired = redis_client.lock('distribution_lock', timeout=30, blocking_timeout=5)
        have_lock = lock_acquired.acquire(blocking=True)
        if have_lock:
            try:
                if redis_client.get('total_leads') is None:
                    reset_daily_counters()

                total_leads = redis_client.incr('total_leads')
                
                consultant_name, user_id = get_next_consultant()

                if not consultant_name:
                    logging.error("Erro ao encontrar um consultor.")
                    return json

                logging.info(f"Consultor atribuído: {consultant_name} (User ID: {user_id})")
                deal_payload = {
                    "deal": {"user_id": user_id, "name": f"{name}"},
                    "contacts": [
                        {
                            "emails": [{"email": email}],
                            "phones": phone_payload,
                            "name": f"{name}",
                        }
                    ],
                }

                rds.CRM().deals().create(data=deal_payload)

     
                logging.info(f"Lead atribuído ao consultor: {consultant_name}")
                return jsonify({"message": "Lead atribuído com sucesso!"}), 200

            finally:
                lock_acquired.release()
        else:
            logging.error("Não foi possível adquirir o lock para distribuição.")
            return jsonify({"error": "Sistema ocupado, tente novamente."}), 503
    else:
        logging.error("Content-Type must be application/json")
        return jsonify({"error": "Content-Type must be application/json"}), 400

@app.route("/stats", methods=["GET"])
def stats():
    total_leads = int(redis_client.get('total_leads') or 0)

    # Leads por consultor
    consultant_counts = {}
    for consultant in CONSULTANTS.keys():
        count = int(redis_client.get(f'consultant_count:{consultant}') or 0)
        consultant_counts[consultant] = count

    return jsonify({
        "total_consultants": len(ALL_CONSULTANTS),
        "total_leads": total_leads,
        "consultants": consultant_counts
    }), 200

@app.route("/reset-db", methods=["GET"])
def reset_db(token=None):
    token = request.args.get("token")
    if token != "sadasd46a4d65sa1d321a3sd1sa23dVv0askL":
        return jsonify({"error": "Token inválido"}), 401

    # limpar apenas o banco de dados do Redis db 2
    redis_client.flushdb(db=2)
    return jsonify({"message": "DB resetado com sucesso!"}), 200

@app.route("/")
def index():
    return "Hello, World!"

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=5000)
