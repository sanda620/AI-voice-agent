from api.payload_client import (
    find_patient_by_name as api_find_patient_by_name,
    find_patient_by_phone as api_find_patient_by_phone,
    register_patient as api_register_patient,
)


async def find_patient_by_name_tool(context, name: str):

    result = await api_find_patient_by_name(name)

    return result



async def find_patient_by_phone_tool(context, phone: str):

    result = await api_find_patient_by_phone(phone)

    return result


async def register_patient_tool(
    context,
    name: str,
    phone: str,
    dob: str,
):

    result = await api_register_patient(
        name=name,
        phone=phone,
        dob=dob,
    )

    return result