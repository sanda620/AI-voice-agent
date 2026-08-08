from typing import Optional

from api.payload_client import (
    get_doctors as api_get_doctors,
    create_appointment as api_create_appointment,
    get_patient_appointments as api_get_patient_appointments,
    cancel_appointment as api_cancel_appointment,
    reschedule_appointment as api_reschedule_appointment,
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

    return result



async def get_patient_appointments_tool(patient_id: str):

    result = await api_get_patient_appointments(patient_id)

    return result



async def cancel_appointment_tool(appointment_id: str):

    result = await api_cancel_appointment(
        appointment_id
    )

    return result



async def reschedule_appointment_tool(
    appointment_id: str,
    date: str,
    time: str,
):

    combined_datetime = f"{date}T{time}:00+05:30"

    result = await api_reschedule_appointment(
        appointment_id,
        combined_datetime,
    )

    return result