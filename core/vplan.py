import xml.etree.ElementTree as ET
from datetime import datetime, date
import locale
import json
import pprint


locale.setlocale(locale.LC_TIME, "de_DE.utf8")
class VPlan:
    dateCreated : datetime
    dateFor : datetime
    freeDays : list[date]
    classPlans : list["ClassPlan"]
    info : list[str] # For some weird unexplainable reason, SP24 sends the info as a list of strings separated by a newline character (\n)

class ClassPlan:
    className : str
    lessons : list["Lesson"]

class Lesson: 
    lessonNumber : int
    subject : str
    teacher : str
    room : str
    info : list[str] = [] # See VPlan.info
    changes : list["Change"] = [] # TODO: Implement changes

class Change:
    originalLesson : Lesson
    subject : str
    teacher : str
    room : str
    info : list[str] = [] # See VPlan.info

class UEPlans:
    dateCreated : datetime
    dateFor : datetime
    freeDays : list[date]
    uePlans : list["UEPlan"]

class UEPlan:
    className : str
    ue : list["Unterrichtseinheit"]

class Unterrichtseinheit:
    subject : str
    teacher : str

def parse_ueplan(xml : str) -> UEPlans:
    root = ET.fromstring(xml)
    ueplans = UEPlans()
    ueplans.freeDays = []
    ueplans.uePlans = []
    ueplans.dateCreated = datetime.strptime(root.find('./Kopf/zeitstempel').text, '%d.%m.%Y, %H:%M')
    ueplans.dateFor = datetime.strptime(root.find('./Kopf/DatumPlan').text, '%A, %d. %B %Y')
    for element in root.findall('./FreieTage/ft'):
        ueplans.freeDays.append(datetime.strptime(f"20{element.text}", '%Y%m%d'))
    for classPlan in root.findall('./Klassen/Kl'):
        cp = UEPlan()
        cp.ue = []
        cp.className = classPlan.find('Kurz').text
        for lesson in classPlan.findall("Unterricht/Ue"):
            print(lesson.items())
            l = Unterrichtseinheit()
            l.subject = (item := lesson.find('UeNr')).get('UeGr',item.get('UeFa'))
            l.teacher = lesson.find('UeNr').get('UeLe')
            cp.ue.append(l)
        ueplans.uePlans.append(cp)

    return ueplans

def parse_vplan(xml : str) -> VPlan:
    root = ET.fromstring(xml)
    vplan = VPlan()
    vplan.freeDays = []
    vplan.classPlans = []
    vplan.info = []

    vplan.dateCreated = datetime.strptime(root.find('./Kopf/zeitstempel').text, '%d.%m.%Y, %H:%M')
    vplan.dateFor = datetime.strptime(root.find('./Kopf/DatumPlan').text, '%A, %d. %B %Y')
    print(root.find('./FreieTage/ft').text)
    for element in root.findall('./FreieTage/ft'):
        vplan.freeDays.append(datetime.strptime(f"20{element.text}", '%Y%m%d'))

    # Parse class plans
    for classPlan in root.findall('./Klassen/Kl'):
        cp = ClassPlan()
        cp.lessons = []
        cp.className = classPlan.find('Kurz').text
        for lesson in classPlan.findall("Pl/Std"):
            l = Lesson()
            l.lessonNumber = int(lesson.find('St').text)
            l.subject = lesson.find('Fa').text
            l.teacher = lesson.find('Le').text
            l.room = lesson.find('Ra').text
            l.info = lesson.find('If').text.split('\n') if lesson.find('If').text else []
            cp.lessons.append(l)
    
        vplan.classPlans.append(cp)
    for element in root.findall('./ZusatzInfo/ZiZeile'):
        vplan.info.append(element.text)

    return vplan