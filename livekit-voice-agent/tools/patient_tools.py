from api.payload_client import (
    find_patient_by_name as api_find_patient_by_name,
    find_patient_by_phone as api_find_patient_by_phone
)


async def find_patient_by_name_tool(context, name: str):

    result = await api_find_patient_by_name(name)

    return result



async def find_patient_by_phone_tool(context, phone: str):

    result = await api_find_patient_by_phone(phone)

    return result