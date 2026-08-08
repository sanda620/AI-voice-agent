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


async def register_patient(
    name: str,
    phone: str,
    dob: str,
):

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{PAYLOAD_URL}/patients",
            json={
                "fullName": name,
                "phone": phone,
                "dateOfBirth": dob,
            },
        )

        if response.status_code >= 400:
            print("PATIENT REGISTRATION ERROR:", response.text)

        response.raise_for_status()

        patient = response.json()

        return {
            "success": True,
            "patient": patient,
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

            print("PAYLOAD ERROR STATUS:", response.status_code)
            print("PAYLOAD ERROR RESPONSE:", response.text)

            try:
                error_data = response.json()
            except Exception:
                error_data = {}

            message = error_data.get(
                "message",
                "Unable to create the appointment."
            )

            return {
                "success": False,
                "message": message,
            }

        return {
            "success": True,
            "appointment": response.json(),
        }



async def get_patient_appointments(patient_id: str):

    async with httpx.AsyncClient() as client:

        response = await client.get(
            f"{PAYLOAD_URL}/appointments",
            params={
                "where[patient][equals]": patient_id,
                "where[status][equals]": "booked",
                "sort": "date",
            },
        )

        response.raise_for_status()

        data = response.json()

        return {
            "success": True,
            "appointments": data["docs"],
        }


async def cancel_appointment(appointment_id: str):

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{PAYLOAD_URL}/cancel-appointment",
            json={
                "appointmentId": appointment_id
            },
        )

        if response.status_code >= 400:

            print(
                "CANCEL ERROR STATUS:",
                response.status_code
            )

            print(
                "CANCEL ERROR RESPONSE:",
                response.text
            )

            try:
                error_data = response.json()
            except Exception:
                error_data = {}

            return {
                "success": False,
                "message": error_data.get(
                    "message",
                    "Unable to cancel the appointment."
                ),
            }

        return response.json()


async def reschedule_appointment(
    appointment_id: str,
    new_date: str,
):

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{PAYLOAD_URL}/reschedule-appointment",
            json={
                "appointmentId": appointment_id,
                "newDate": new_date,
            },
        )

        if response.status_code >= 400:

            print(
                "RESCHEDULE ERROR STATUS:",
                response.status_code
            )

            print(
                "RESCHEDULE ERROR RESPONSE:",
                response.text
            )

            try:
                error_data = response.json()
            except Exception:
                error_data = {}

            return {
                "success": False,
                "message": error_data.get(
                    "message",
                    "Unable to reschedule the appointment."
                ),
            }

        return response.json()