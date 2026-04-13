import spacy
import boto3
import time
import os
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
            print("Avís: DynamoDB no disponible localment.")
            self.table = None

    def analyze_intent(self, text):
        if not nlp: return "error_model", []
        doc = nlp(text)
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        
        intent = "consulta_general"
        lower_text = text.lower()
        if any(w in lower_text for w in ["comanda", "pedido", "estat", "order"]):
            intent = "estat_comanda"
        elif any(w in lower_text for w in ["preu", "precio", "cost", "quant"]):
            intent = "consulta_preu"
            
        return intent, entities

    def save_to_history(self, session_id, user_text, bot_response):
        if self.table:
            try:
                self.table.put_item(
                    Item={
                        'SessionID': session_id,
                        'Timestamp': int(time.time()),
                        'UserText': user_text,
                        'BotResponse': bot_response,
                        'Date': datetime.now().isoformat()
                    }
                )
            except:
                pass

    def respond(self, session_id, text):
        intent, entities = self.analyze_intent(text)
        
        if intent == "estat_comanda":
            response = "Estic revisant l'estat del teu lliurament... Segons la IA, el teu repartidor està a punt d'arribar."
        elif intent == "consulta_preu":
            response = "M'has preguntat pel preu. Els costos varien, però per aquesta zona el lliurament és de 2.50€."
        else:
            if entities:
                response = f"Entenc la teva consulta sobre {entities[0][0]}. Com et puc ajudar més?"
            else:
                response = "Hola! Com puc ajudar-te amb la teva operació de Glovo?"

        self.save_to_history(session_id, text, response)
        return response

# Inicialització de Flask
app = Flask(__name__, static_folder='.')
CORS(app)
bot = GlovoChatbot()

# Ruta per servir la web principal
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Ruta per servir el CSS i altres arxius estàtics
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
    print("\n" + "="*40)
    print("PROYECTO GLOVO: TRANSFORMACIÓN DIGITAL")
    print("="*40)
    print("Servidor actiu a: http://localhost:5000")
    print("Ja pots obrir aquesta URL al teu navegador!")
    print("Prem Ctrl+C per aturar el servidor.")
    print("="*40 + "\n")
    app.run(port=5000, debug=False)
