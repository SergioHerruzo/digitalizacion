# Projecte de Transformació Digital - Glovo (AWS Academy)

Aquest repositori conté el Pla d'Implementació i els components tècnics per a la transformació digital de Glovo, enfocat en IA, Big Data i infraestructura Cloud.

## Continguts del Projecte
- **[Pla_Implementacio_Glovo.md](Pla_Implementacio_Glovo.md)**: El document mestre amb la diagnosi DAFO, estratègia de dades, KPIs i conclusions.
- **[main.tf](main.tf)**: Configuració de Terraform per a la infraestructura d'AWS (EC2, S3, DynamoDB) utilitzant el `LabRole`.
- **[chatbot.py](chatbot.py)**: Motor del xatbot en Python amb capacitats de NLP (spaCy/NLTK).
- **[requirements.txt](requirements.txt)**: Dependències de Python.
- **[index.html](index.html) i [styles.css](styles.css)**: Mockup de la interfície web premium per a AWS Amplify.

## Arquitectura de la Solució
1.  **Frontend**: Allotjat a AWS Amplify (PaaS).
2.  **Motor d'IA**: Instància EC2 amb Python i spaCy per a l'anàlisi d'intencions.
3.  **Dades**: 
    *   **DynamoDB**: Persistència de l'historial del xat i dades del CRM.
    *   **S3**: Emmagatzematge de logs i dades no estructurades.
4.  **Optimització**: Algoritmes d'IA per al càlcul de rutes segons trànsit i clima.

## Requisits d'Instal·lació
```bash
pip install -r requirements.txt
python -m spacy download es_core_news_md
```

## Seguretat
Projecte configurat per a l'entorn **AWS Academy Learner Lab**. S'ha de garantir l'ús del `LabRole` i `LabInstanceProfile`.
