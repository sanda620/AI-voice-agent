from urllib import response

import httpx


PAYLOAD_URL = "http://localhost:3000/api"


async def find_patient_by_name(name: str):

    async with httpx.AsyncClient() as client:

        response = await client.get(
            f"{PAYLOAD_URL}/patients",
            params={
                "where[fullName][contains]": name
            }
        )

        response.raise_for_status()

        data = response.json()

        if data["totalDocs"] > 0:

            return {
                "found": True,
                "patient": data["docs"][0]
            }

        return {
            "found": False,
            "patient": None
        }



async def find_patient_by_phone(phone: str):

    async with httpx.AsyncClient() as client:

        response = await client.get(
            f"{PAYLOAD_URL}/patients",
            params={
                "where[phone][equals]": phone
            }
        )

        response.raise_for_status()

        data = response.json()

        if data["totalDocs"] > 0:

            return {
                "found": True,
                "patient": data["docs"][0]
            }

        return {
            "found": False,
            "patient": None
        }



async def get_doctors():

    async with httpx.AsyncClient() as client:

        response = await client.get(
            f"{PAYLOAD_URL}/doctors"
        )

        response.raise_for_status()

        data = response.json()

        return {
            "doctors" : data["docs"]
        }



async def create_appointment(appointment_data: dict):

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{PAYLOAD_URL}/appointments",
            json=appointment_data
        )
        if response.status_code >= 400:
            print("PAYLOAD ERROR RESPONSE:", response.text)

        response.raise_for_status()

        return response.json()
