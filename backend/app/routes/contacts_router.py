"""
Contacts router — serves beneficial official legal contacts.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.config.contacts import BENEFICIAL_CONTACTS, ContactInfo

router = APIRouter(prefix="/api/v1/contacts", tags=["contacts"])


class ContactsResponse(BaseModel):
    contacts: list[ContactInfo]


@router.get("", response_model=ContactsResponse)
async def get_beneficial_contacts():
    """Get a list of official Georgian legal and public service contacts."""
    return ContactsResponse(contacts=BENEFICIAL_CONTACTS)
