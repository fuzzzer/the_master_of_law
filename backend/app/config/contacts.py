"""
Static registry of official Georgian legal and public service contacts.
"""

from pydantic import BaseModel


class ContactInfo(BaseModel):
    name: str
    description: str
    phone: str
    email: str
    address: str
    website: str


BENEFICIAL_CONTACTS = [
    ContactInfo(
        name="შსს გენერალური ინსპექცია",
        description="პოლიციის თანამშრომელთა მხრიდან გადაცდომის, უფლებამოსილების გადამეტების ან არამართლზომიერი ქმედების გასაჩივრებისთვის.",
        phone="126",
        email="gen126@mia.gov.ge",
        address="თბილისი, გ. გულუას ქ. №10",
        website="https://police.ge",
    ),
    ContactInfo(
        name="სპეციალური საგამოძიებო სამსახური",
        description="სამართალდამცავთა მიერ ჩადენილი დანაშაულის (წამება, არაადამიანური მოპყრობა) დამოუკიდებელი გამოძიებისთვის.",
        phone="199",
        email="office@sis.gov.ge",
        address="თბილისი, მ. ასათიანის ქ. №9",
        website="https://sis.gov.ge",
    ),
    ContactInfo(
        name="სახალხო დამცველი (ომბუდსმენი)",
        description="ადამიანის უფლებათა და თავისუფლებათა დარღვევის ფაქტებზე რეაგირებისთვის.",
        phone="1481",
        email="info@ombudsman.ge",
        address="თბილისი, ირაკლი ფაღავას ქ. N6, 0144",
        website="https://ombudsman.ge",
    ),
    ContactInfo(
        name="პერსონალურ მონაცემთა დაცვის სამსახური",
        description="თქვენი პერსონალური მონაცემების უკანონო დამუშავების, ვიდეო/აუდიო ჩანაწერების გასაჩივრებისთვის.",
        phone="242 1000",
        email="office@pdps.ge",
        address="თბილისი, ვაჟა-ფშაველას გამზ. №71, ბლოკი 1, მე-2 სართული",
        website="https://pdps.ge",
    ),
    ContactInfo(
        name="იურიდიული დახმარების სამსახური",
        description="უფასო იურიდიული კონსულტაცია და ადვოკატის მომსახურება გადახდისუუნარო პირთათვის.",
        phone="1485",
        email="info@legalaid.ge",
        address="თბილისი, აღმაშენებლის გამზ. №140ა",
        website="https://legalaid.ge",
    ),
]
