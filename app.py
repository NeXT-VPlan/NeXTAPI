from flask import Flask, json, jsonify, request
import requests
from xml.etree.ElementTree import ElementTree, Element
from flask_sqlalchemy import SQLAlchemy
from datetime import date, timedelta
from core.vplan import parse_vplan, parse_ueplan
from pprint import pformat
import hashlib
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///keys.db'

db = SQLAlchemy(app)

class SP24Access(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    schulnummer = db.Column(db.String(8), nullable=False)
    nutzer = db.Column(db.String(10), nullable=False)
    passwort = db.Column(db.String(1024), nullable=False)
    instance = db.Column(db.String(256), nullable=False)
    accessKey = db.Column(db.String(256), nullable=False, unique=True)

    def __repr__(self):
        return '<SP24Access %r>' % self.schulnummer
    
@app.route('/api/v1/sp24profiles/<schulnummer>', methods=['GET'])
def get_sp24profiles(schulnummer):
    sp24access = SP24Access.query.filter_by(schulnummer=schulnummer).first()
    if sp24access is None:
        print("Not found")
        return jsonify({'error': 'Not found'}), 404
    if request.headers.get('X-Access-Key', ) != sp24access.accessKey:
        return jsonify({'error': 'Unauthorized'}), 401
    dt = date.today()
    if dt.weekday() == 5:
        dt = dt + timedelta(days=2)
    elif dt.weekday() == 6:
        dt = dt + timedelta(days=1)
    url = f"https://{sp24access.instance}/{schulnummer}/wplan/wdatenk/WPlanKl_{request.args.get('date',dt.strftime('%Y%m%d'))}.xml"
    r = requests.get(url,
                     auth=requests.auth.HTTPBasicAuth(sp24access.nutzer, sp24access.passwort))
    
    if r.status_code != 200:
        print(r.text)
        print("????")
        return jsonify({'error': 'Failed to fetch data', 'content': r.text}), r.status_code
    
    plan = parse_ueplan(r.text)
    if request.args.get("classes"):
        for classPlan in plan.classPlans:
            if classPlan.className not in request.args.get("classes").split(","):
                plan.classPlans.remove(classPlan)
    for i, freeDay in enumerate(plan.freeDays):
        plan.freeDays[i] = freeDay.isoformat()
    plan.dateCreated = plan.dateCreated.isoformat()
    plan.dateFor = plan.dateFor.isoformat()
    for i, cplan in enumerate(plan.uePlans):
        for j, lesson in enumerate(cplan.lessons):
            cplan.ue[j] = lesson.__dict__
        plan.uePlans[i] = cplan.__dict__
    
    return json.dumps(plan.__dict__)


@app.route('/api/v1/sp24plan/<schulnummer>', methods=['GET'])
def get_sp24access(schulnummer):
    sp24access = SP24Access.query.filter_by(schulnummer=schulnummer).first()
    if sp24access is None:
        print("Not found")
        return jsonify({'error': 'Not found'}), 404
    if request.headers.get('X-Access-Key', ) != sp24access.accessKey:
        return jsonify({'error': 'Unauthorized'}), 401
    dt = date.today()
    if dt.weekday() == 5:
        dt = dt + timedelta(days=2)
    elif dt.weekday() == 6:
        dt = dt + timedelta(days=1)
    url = f"https://{sp24access.instance}/{schulnummer}/mobil/mobdaten/PlanKl{request.args.get('date',dt.strftime('%Y%m%d'))}.xml"
    r = requests.get(url,
                     auth=requests.auth.HTTPBasicAuth(sp24access.nutzer, sp24access.passwort))
    
    if r.status_code != 200:
        print(r.text)
        print("????")
        return jsonify({'error': 'Failed to fetch data'}), 500
    
    plan = parse_vplan(r.text)
    if request.args.get("classes"):
        for classPlan in plan.classPlans:
            if classPlan.className not in request.args.get("classes").split(","):
                plan.classPlans.remove(classPlan)
    for i, freeDay in enumerate(plan.freeDays):
        plan.freeDays[i] = freeDay.isoformat()
    plan.dateCreated = plan.dateCreated.isoformat()
    plan.dateFor = plan.dateFor.isoformat()
    for i, cplan in enumerate(plan.classPlans):
        for j, lesson in enumerate(cplan.lessons):
            cplan.lessons[j] = lesson.__dict__
        plan.classPlans[i] = cplan.__dict__
    
    print("okie dokie")
    return json.dumps(plan.__dict__)

@app.route('/api/v1/sp24access', methods=['POST'])
def create_sp24access():
    data = request.get_json()
    schulnummer = data.get('schulnummer')
    nutzer = data.get('nutzer')
    passwort = data.get('passwort')
    instance = "www.stundenplan24.de"
    print(nutzer,passwort,schulnummer,instance)
    dt = date.today()
    if dt.weekday() == 5:
        dt = dt + timedelta(days=2)
    elif dt.weekday() == 6:
        dt = dt + timedelta(days=1)
    # Perform authentication and validation of credentials here
    r = requests.head(f"https://{instance}/{schulnummer}/mobil/mobdaten/PlanKl{dt.strftime('%Y%m%d')}.xml",
                     auth=requests.auth.HTTPBasicAuth(nutzer, passwort))
    print(r.status_code,r.text)
    if not r.ok:
        return jsonify({'error': 'Invalid credentials'}), 401
    sp24access = SP24Access.query.filter_by(schulnummer=schulnummer).first()
    if sp24access is not None:
        return jsonify({'accessKey': sp24access.accessKey}), 200
    # Generate a secure access key
    accessKey = hashlib.sha256(f"{schulnummer}:{nutzer}:{passwort}:{instance}:{str(uuid.uuid4())}".encode('utf-8')).hexdigest()
    
    # Save the SP24Access object to the database
    sp24access = SP24Access(schulnummer=schulnummer, nutzer=nutzer, passwort=passwort, instance=instance, accessKey=accessKey)
    db.session.add(sp24access)
    db.session.commit()
    
    return jsonify({'accessKey': accessKey}), 201

if __name__ == '__main__':
    app.run(port=8080,debug=True)