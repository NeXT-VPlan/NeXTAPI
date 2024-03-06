from flask import Flask, json, jsonify, request
import requests
from xml.etree.ElementTree import ElementTree, Element
from flask_sqlalchemy import SQLAlchemy
from datetime import date
from core.vplan import parse_vplan
from pprint import pformat
import hashlib

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///keys.db'

db = SQLAlchemy(app)

class SP24Access(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    schulnummer = db.Column(db.String(8), unique=True, nullable=False)
    nutzer = db.Column(db.String(10), nullable=False)
    passwort = db.Column(db.String(1024), nullable=False)
    instance = db.Column(db.String(256), nullable=False)
    accessKey = db.Column(db.String(256), nullable=False, unique=True)

    def __repr__(self):
        return '<SP24Access %r>' % self.schulnummer
    
@app.route('/api/v1/sp24plan/<schulnummer>', methods=['GET'])
def get_sp24access(schulnummer):
    sp24access = SP24Access.query.filter_by(schulnummer=schulnummer).first()
    if sp24access is None:
        return jsonify({'error': 'Not found'}), 404
    if request.headers.get('X-Access-Key', ) != sp24access.accessKey:
        return jsonify({'error': 'Unauthorized'}), 401
    url = f"https://{sp24access.instance}/{schulnummer}/mobil/mobdaten/PlanKl{request.args.get('date',date.today().strftime('%Y%m%d'))}.xml"
    r = requests.get(url,
                     auth=requests.auth.HTTPBasicAuth(sp24access.nutzer, sp24access.passwort))
    
    if r.status_code != 200:
        return jsonify({'error': 'Failed to fetch data'}), 500
    plan = parse_vplan(r.text)
    if request.args.get("classes"):
        for classPlan in plan.classPlans:
            if classPlan.className not in request.args.get("classes").split(","):
                plan.classPlans.remove(classPlan)
    return pformat(plan.__dict__)

@app.route('/api/v1/sp24access', methods=['POST'])
def create_sp24access():
    data = request.get_json()
    schulnummer = data.get('schulnummer')
    nutzer = data.get('nutzer')
    passwort = data.get('passwort')
    instance = data.get('instance')
    
    # Perform authentication and validation of credentials here
    r = requests.head(f"https://{instance}/{schulnummer}/mobil/mobdaten/PlanKl{date.today().strftime('%Y%m%d')}.xml",
                     auth=requests.auth.HTTPBasicAuth(nutzer, passwort))
    if not r.ok:
        return jsonify({'error': 'Invalid credentials'}), 401
    # Generate a secure access key
    accessKey = hashlib.sha256(f"{schulnummer}:{nutzer}:{passwort}:{instance}".encode('utf-8')).hexdigest()
    
    # Save the SP24Access object to the database
    sp24access = SP24Access(schulnummer=schulnummer, nutzer=nutzer, passwort=passwort, instance=instance, accessKey=accessKey)
    db.session.add(sp24access)
    db.session.commit()
    
    return jsonify({'accessKey': accessKey}), 201