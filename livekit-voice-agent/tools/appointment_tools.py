from typing import Optional

from api.payload_client import (
    get_doctors as api_get_doctors,
    create_appointment as api_create_appointment
)



async def get_available_doctors(context):

    result = await api_get_doctors()

    return result



async def create_appointment_tool(
    patient_id: str,
    doctor_id: str,
    date: str,
    time: str,
    notes: Optional[str] = ""
    ):

    combined_datetime = f"{date}T{time}:00+05:30"
    appointment_data = {

        "patient": patient_id,

        "doctor": doctor_id,

        "date": combined_datetime,

    }


    if notes:
        appointment_data["notes"] = notes


    result = await api_create_appointment(
        appointment_data
    )


    return {
        "success": True,
        "appointment": result
    }