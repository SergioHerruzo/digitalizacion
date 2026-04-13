# Pla d'Implementació de Transformació Digital: Glovo
**Consultoria: Antigravity Digital Solutions**  
**Data:** 13 d'abril de 2026  
**Client:** Glovo App  

---

## 1. Diagnosi DAFO: Glovo com a Plataforma d'Economia Digital

Glovo s'ha consolidat com un referent en l'economia de plataformes, actuant com un mercat tripartit que connecta usuaris, socis comercials i repartidors. Tot i la seva posició dominant, la transformació digital és imperativa per mantenir la rendibilitat i l'eficiència operativa.

| **Fortaleses** | **Debilitats** |
| :--- | :--- |
| Versatilitat "Anything": no només lliurament de menjar. | Complexitat operativa extremadament alta. |
| Fort efecte de xarxa en centres urbans densos. | Marges unitaris baixos que depenen del volum massiu. |
| Algorismes avançats de logística ja en funcionament. | Dependència de la regulació laboral externa. |

| **Oportunitats** | **Amenaces** |
| :--- | :--- |
| Expansió del Quick-Commerce (Q-commerce) amb Dark Stores. | Legislació laboral més estricta (ex. Ley Rider). |
| Hyper-personalització mitjançant IA i Big Data. | Competència feroç de gegants com Uber Eats o Deliveroo. |
| Logística com a Servei (B2B) per a terceres empreses. | Inestabilitat econòmica que redueix el consum discrecional. |

---

## 2. Estratègia de Dades: Big Data (5Vs) i CRM

L'eix vertebrador d'aquest projecte és la captura de dades massives a través del nou xatbot intel·ligent per alimentar el CRM i personalitzar l'experiència de l'usuari seguint el model de les **5Vs**:

1.  **Volum:** El xatbot processarà milers de consultes simultànies, generant un flux continu de dades transaccionals i de comportament.
2.  **Velocitat:** Processament en temps real per respondre a les inquietuds del client i ajustar les ofertes en segons.
3.  **Varietat:** Combinació de text lliure (NLP), historial de comandes, geolocalització i dades meteorològiques.
4.  **Veracitat:** Neteja de dades mitjançant IA per filtrar soroll i assegurar que les preferències detectades són autèntiques.
5.  **Valor:** Conversions de dades brutes en "insights" accionables per al CRM, permetent promocions predictives (ex. oferir un descompte en cafè a algú que sempre demana el matí).

---

## 3. Optimització de Rutes: El Sistema d'IA Logística

El nou motor d'IA s'especialitza en l'anàlisi predictiva per millorar la logística d'última milla:

*   **Anàlisi de Trànsit:** Integració d'APIs de trànsit en temps real per recalcular rutes cada 30 segons.
*   **Variable Meteorològica:** L'algoritme preveu retards per pluja o condicions extremes, ajustant automàticament les finestres de lliurament comunicades a l'usuari i suggerint rutes més segures o ràpides per als repartidors.
*   **Balanceig de Càrrega:** Predicció de pics de demanda per zones, posicionant els "Glovers" de manera proactiva en punts calents abans que es realitzin les comandes.

---

## 4. Interfície Web: Allotjament amb AWS Amplify

La nova interfície d'estil Glovo s'implementarà com una Single Page Application (SPA), utilitzant **AWS Amplify** per a l'allotjament i la gestió del cicle de vida:

*   **Model PaaS (Platform as a Service):** Amplify automatitza el desplegament des del repositori de Git (CI/CD), gestionant certificats SSL, CDN (CloudFront) i l'escalabilitat sense intervenció manual.
*   **Integració Frontend-Backend:** Mitjançant l'Amplify SDK, la web es comunica de forma nativa amb el xatbot (allotjat en EC2) i les bases de dades (DynamoDB), simplificant l'autenticació i el subministrament de recursos.
*   **Agilitat UX:** Permet versions de prova ("feature branches") per validar nous dissenys d'interfície abans de passar a producció.

---

## 5. Xatbot Propi: Inteligència Artificial en Python

El cor de l'atenció al client i la recollida de dades és un xatbot desenvolupament íntegrament en **Python**, utilitzant biblioteques especialitzades de Processament del Llenguatge Natural (NLP):

*   **Motor NLP (spaCy / NLTK):**
    *   **spaCy:** Utilitzat per a l'extracció d'entitats (NER) i l'anàlisi de dependències sintàctiques en temps real.
    *   **NLTK:** Empleat per a la tokenització i la classificació d'intencions (intent classification) més granular.
*   **Lògica de Negoci:** El bot no només respon dubtes, sinó que interactua amb l'API de Glovo per consultar estats de comandes i suggerir productes basats en el context de la conversa.
*   **Exemple de flux en Python:**
    ```python
    import spacy
    nlp = spacy.load("es_core_news_md")

    def process_user_input(text):
        doc = nlp(text)
        # Extracció d'intencions i entitats per al CRM
        for ent in doc.ents:
            print(f"Detectat: {ent.text} ({ent.label_})")
        return "Com puc ajudar-te amb la teva comanda a " + [e.text for e in doc.ents if e.label_ == 'LOC'][0]
    ```

---

## 6. Infraestructura d'AWS amb Terraform

Per garantir la reproductibilitat i el control de costos dins del **AWS Academy Learner Lab**, s'utilitza **Terraform** (Infrastructure as Code).

### Restricció de Seguretat Crítica
Tots els recursos utilitzaran el **LabRole** preexistent. No es crearan nous rols d'IAM per evitar conflictes de permisos en l'entorn de laboratori.

### Codi HCL (Terraform)
```hcl
# Configuració de la instància EC2 per al motor de Python
resource "aws_instance" "chatbot_engine" {
  ami           = "ami-0c55b159cbfafe1f0" # Amazon Linux 2
  instance_type = "t2.micro"
  iam_instance_profile = "LabInstanceProfile" # Ús del LabRole

  tags = {
    Name = "Glovo-Chatbot-Engine"
  }
}

# Emmagatzematge S3 per a dades no estructurades (imatges, logs)
resource "aws_s3_bucket" "glovo_data_assets" {
  bucket = "glovo-transf-digital-assets-unique-id"
}

# Persistència de converses en DynamoDB
resource "aws_dynamodb_table" "chat_history" {
  name           = "GlovoChatHistory"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "SessionID"

  attribute {
    name = "SessionID"
    type = "S"
  }
}
```

---
