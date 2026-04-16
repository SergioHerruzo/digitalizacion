import spacy
import boto3
import json
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
        # Memòria temporal per a les sessions (Context)
        self.sessions_context = {} 
        try:
            self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            self.table = self.dynamodb.Table('GlovoChatHistory')
        except:
            self.table = None
            
        # Banc de preguntes freqüents (FAQ)
        self.faq_bank = []
        self.faq_docs = []
        try:
            with open('faq.json', 'r', encoding='utf-8') as f:
                self.faq_bank = json.load(f)
            # Pre-processem les preguntes per a més velocitat en la similitud
            if nlp:
                self.faq_docs = [(nlp(item['question']), item['answer']) for item in self.faq_bank]
        except Exception as e:
            print(f"Error carregant el banc de FAQs: {e}")

    def analyze_intent(self, text, session_id):
        if not nlp: return "error_model", []
        doc = nlp(text)
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        lower_text = text.lower()
        
        # Gestió de CONTEXT (Prioritat màxima)
        context = self.sessions_context.get(session_id)
        if context == "esperant_resolucio":
            if any(w in lower_text for w in ["dinero", "diners", "tornem", "reembors", "reembolso", "dame"]):
                return "resolucio_diners", entities
            elif any(w in lower_text for w in ["portem", "traer", "nou", "nuevo", "enviar", "repetir"]):
                return "resolucio_producte", entities

        # Diccionari d'intents avançat (ordenat per prioritat semàntica)
        intents_config = [
            ("retard", ["tarde", "retraso", "demora", "no llega", "no arriba", "tarda", "demasiado"]),
            ("incidencia", ["falta", "faltan", "malament", "mal", "equivocat", "equivocado", "reclamar", "problema", "no és"]),
            ("salutacio", ["hola", "buenos dias", "bon dia", "bones", "hey", "qué tal", "que tal"]),
            # Estat de la comanda (prioritat sobre preus quan es pregunta pel temps)
            ("comanda_status", ["comanda", "pedido", "estat", "order", "arriba", "on està", "dónde está", "seguiment", "queda", "falta", "cuánto le", "cuanto le", "donde", "lligues"]),
            # Preus (fem que 'cuanto' per si sol no sigui suficient si no hi ha kws de preu)
            ("preu_info", ["preu", "precio", "cost", "quant costa", "cuanto cuesta", "tarif", "valer", "vale", "diners"]),
            ("humor_fact", ["broma", "chiste", "curiositat", "curiosidad", "sabies", "sabías", "cuéntame algo"]),
            ("agraïment", ["gràcies", "gracias", "merci", "perfecte", "ok", "crack", "guay"]),
            ("comiat", ["adeu", "adiós", "ciao", "fins després", "bye", "chao"])
        ]

        detected_intent = "consulta_general"
        for intent, keywords in intents_config:
            if any(kw in lower_text for kw in keywords):
                detected_intent = intent
                break
            
        return detected_intent, entities

    def find_faq_answer(self, text):
        if not nlp or not self.faq_docs:
            return None
            
        user_doc = nlp(text)
        best_match = None
        highest_similarity = 0
        
        for faq_doc, answer in self.faq_docs:
            sim = user_doc.similarity(faq_doc)
            if sim > highest_similarity:
                highest_similarity = sim
                best_match = answer
        
        # Llindar de similitud (0.75 sembla raonable per a frases curtes)
        if highest_similarity > 0.75:
            return best_match
            
        return None

    def estimate_time(self, location):
        loc_lower = location.lower()
        if "barcelona" in loc_lower: return random.randint(15, 25)
        if any(city in loc_lower for city in ["madrid", "valència", "sevilla"]): return random.randint(25, 40)
        return random.randint(20, 50)

    def respond(self, session_id, text):
        intent, entities = self.analyze_intent(text, session_id)
        locations = [e[0] for e in entities if e[1] == 'LOC']
        
        # --- MOTOR DE RESPOSTES MINI-GEMINI ---
        
        if intent == "retard":
            responses = [
                f"Deixa'm que miri el mapa... 🗺️ Ostres, si que anem una mica tard per {locations[0] if locations else 'aquí'}. Hi ha una mica de trànsit, però el teu repartidor està fent tot el possible! Et demano una mica de paciència, et compensarem pel retard! 😉",
                "Ostres! Sap greu la demora. ⏳ Estic consultant el GPS i veig que el repartidor està a pocs carrers. S'ha hagut de desviar una mica però arriba en breu. No et preocupis!"
            ]
            return random.choice(responses)

        elif intent == "incidencia":
            self.sessions_context[session_id] = "esperant_resolucio"
            return "Vaja, sap greu sentir això! 😟 Que et faltin coses no m'agrada gens. Estic obrint un tiquet d'incidència ara mateix. Digue'm, vols que et tornem els diners del que falta o prefereixes que te'ls portem de nou a casa?"

        elif intent == "resolucio_diners":
            self.sessions_context[session_id] = None
            return "Fet! 💸 Ja hem tramitat el reemborsament proporcional directament al teu compte. El tindràs en un màxim de 48h. Sento de nou el problema, et mereixes una bona experiència!"

        elif intent == "resolucio_producte":
            self.sessions_context[session_id] = None
            return "D'acord! 🛵 Acabo d'avisar a un repartidor perquè et porti els productes que falten corrents. Arribarà en un obrir i tancar d'ulls! Gràcies per ser tan pacient amb nosaltres."

        elif intent == "salutacio":
            salutacions = [
                "Hola! Com va això? 😊 Sóc el teu assistent de Glovo, en què et puc ajudar avui?",
                "Ei! Què tal et va el dia? Passava per aquí per si necessitaves qualsevol cosa amb la teva comanda. Digue'm!",
                "Hola! Què et ve de gust avui? Tens alguna consulta o vols demanar alguna cosa?"
            ]
            return random.choice(salutacions)
        
        elif intent == "comanda_status":
            if locations:
                time_est = self.estimate_time(locations[0])
                return f"Mirant la teva zona de {locations[0]}... 📍 Veig que els lliuraments van ràpid, uns {time_est} minuts aproximadament. El teu repartidor està a punt per volar!"
            else:
                return "Estic consultant la base de dades... 🔍 Veig que la teva comanda està en marxa i arribarà molt aviat. Si em dius la teva ciutat, et puc donar un temps més exacte!"

        elif intent == "preu_info":
            return "Doncs mira, t'explico: el preu depèn de la distància, però sol rondar els 1.50€ - 3€. 💶 Ara mateix tenim algunes promocions, vols que et busqui codis de descompte?"
            
        elif intent == "humor_fact":
            facts = [
                "Sabies que el producte més demanat a Glovo durant la pandèmia van ser els plàtans? 🍌 Curuós, oi?",
                "Dada curiosa: La comanda més gran de la història de Glovo va portar més de 100 hamburgueses per una festa! 🍔 Vaja gana!",
                "Un acudit? Per què els de Glovo no juguen a l'amagatall? Perquè sempre els acaben trobant pel GPS! 😂 (Molt dolent, ho sé...)"
            ]
            return random.choice(facts)

        elif intent == "agraïment":
            return "De res! 🙌 Ja saps on sóc si em necessites. Disfruta de la comanda!"
            
        elif intent == "comiat":
            return "Vinga, que vagi molt bé! Fins la propera vegada que tinguis gana! 👋"
            
        else:
            # Abans de donar el fallback, intentem buscar al banc de FAQs
            faq_answer = self.find_faq_answer(text)
            if faq_answer:
                return faq_answer

            # Fallback amb estil "Gemini"
            if locations:
                time_est = self.estimate_time(locations[0])
                return f"Entenc que em parles de {locations[0]} 🌍. Encara estic aprenent, però sé que allà entreguem en uns {time_est} minuts. Però... exactament què necessites saber?"
            elif len(text.split()) > 1:
                return f"M'estàs explicant una cosa molt interessant sobre '{text.split()[0]}'... 🤔 Però encara sóc un bot jove i no et segueixo del tot. Em preguntaves per una comanda, pel preu o volies que t'expliqués una curiositat?"
            else:
                return "Ostres, no t'he acabat d'entendre 😅. Pots preguntar-me on està el teu pedido, què costa l'enviament o simplement saludar-me!"

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
    print("🚀 GLOVO CHATBOT: VERSIÓ MINI-GEMINI")
    print("="*50)
    print("Servidor actiu a: http://localhost:5000")
    print("Estil: Modern i proper (Tuteig) 😊")
    print("="*50 + "\n")
    app.run(port=5000, debug=False)
