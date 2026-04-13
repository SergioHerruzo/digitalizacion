import spacy
import boto3
import time
import os
import random
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Carreguem el model d'idioma català/espanyol
try:
    nlp = spacy.load("es_core_news_md")
except:
    print("Recordeu instal·lar el model: py -3.12 -m spacy download es_core_news_md")
    nlp = None

class GlovoChatbot:
    def __init__(self):
        try:
            self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            self.table = self.dynamodb.Table('GlovoChatHistory')
        except:
            self.table = None

    def analyze_intent(self, text):
        if not nlp: return "error_model", []
        doc = nlp(text)
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        
        lower_text = text.lower()
        
        # Diccionari de paraules clau per intents
        intents = {
            "salutacio": ["hola", "buenos dias", "bon dia", "bones", "hey", "qué tal"],
            "comanda_status": ["comanda", "pedido", "estat", "order", "arriba", "on està", "dónde está"],
            "preu_info": ["preu", "precio", "cost", "quant", "cuanto", "tarif"],
            "agraïment": ["gràcies", "gracias", "merci", "perfecte", "ok"],
            "comiat": ["adeu", "adiós", "ciao", "fins després"]
        }

        detected_intent = "consulta_general"
        for intent, keywords in intents.items():
            if any(kw in lower_text for kw in keywords):
                detected_intent = intent
                break
            
        return detected_intent, entities

    def estimate_time(self, location):
        """Simula una estimació segons la ubicació."""
        loc_lower = location.lower()
        if "barcelona" in loc_lower:
            return random.randint(15, 25)
        elif any(city in loc_lower for city in ["madrid", "valència", "sevilla", "bilbao"]):
            return random.randint(25, 40)
        return random.randint(20, 50)

    def respond(self, session_id, text):
        intent, entities = self.analyze_intent(text)
        locations = [e[0] for e in entities if e[1] == 'LOC']
        
        # Respostes amb personalitat i cercania 💛
        if intent == "salutacio":
            response = "Hola! Què tal? 😊 Sóc l'assistent de Glovo. En què et puc ajudar avui per fer-te la vida una mica més fàcil?"
        
        elif intent == "comanda_status":
            if locations:
                time_est = self.estimate_time(locations[0])
                response = f"D'acord! Veig que parles de {locations[0]}. 📍 Per aquesta zona el temps estimat és d'uns {time_est} minuts. El teu repartidor s'està preparant!"
            else:
                response = "Estic mirant-ho ara mateix! 🔍 Segons el sistema, la teva comanda està en camí i arribarà molt aviat. Vols que t'ajudi amb la ubicació exacta?"
        
        elif intent == "preu_info":
            response = "Mira, t'explico: els preus varien una mica segons la distància, però normalment per aquí el lliurament costa entre 1.50€ i 3€. Vols que calculi el preu de l'enviament per a la teva zona?"
            
        elif intent == "agraïment":
            response = "No es mereixen! 🙌 M'encanta poder ajudar-te. Tens cap altra dubte o ja està tot a punt?"
            
        elif intent == "comiat":
            response = "Que vagi molt bé! Fins la propera vegada que tinguis gana o necessitis qualsevol cosa. 👋"
            
        else:
            # Fallback contextual
            if locations:
                time_est = self.estimate_time(locations[0])
                response = f"Oh, veig que estàs per {locations[0]}! 🌍 Sabies que allà el temps de lliurament és de només {time_est} minuts? Què t'agradaria demanar?"
            elif len(text.split()) > 1:
                response = f"Molt interessant el que dius... 🤔 Sembla que em parles de '{text.split()[0]}', però encara estic aprenent. Em podries donar una mica més de context?"
            else:
                response = "Em sap greu, no estic segur de com ajudar-te amb això encara 😅. Pots preguntar-me per la teva comanda, preus o dir-me on et trobes!"

        self.save_to_history(session_id, text, response)
        return response

    def save_to_history(self, session_id, user_text, bot_response):
        if self.table:
            try:
                self.table.put_item(
                    Item={
                        'SessionID': session_id, 'Timestamp': int(time.time()),
                        'UserText': user_text, 'BotResponse': bot_response,
                        'Date': datetime.now().isoformat()
                    }
                )
            except: pass

# Inicialització de Flask
app = Flask(__name__, static_folder='.')
CORS(app)
bot = GlovoChatbot()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_text = data.get('text', '')
    session_id = data.get('session_id', 'local_user')
    response_text = bot.respond(session_id, user_text)
    return jsonify({'reply': response_text, 'status': 'success'})

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 PROYECTO GLOVO: TRANSFORMACIÓN DIGITAL (VERSIÓ PRO)")
    print("="*50)
    print("Servidor actiu a: http://localhost:5000")
    print("To de veu: Proper i amable 😊")
    print("Localització focus: Barcelona 📍")
    print("="*50 + "\n")
    app.run(port=5000, debug=False)
