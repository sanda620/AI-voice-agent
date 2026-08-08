import datetime
import logging
import time
import os

from dotenv import load_dotenv
from datetime import datetime
from typing import Optional

from livekit import agents
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    room_io,
    AgentStateChangedEvent,
    MetricsCollectedEvent,
    metrics,
    function_tool,
    RunContext,
)
from livekit.agents import llm, stt, tts, inference

from livekit.plugins import (
    noise_cancellation,
    silero,
)

from livekit.plugins.turn_detector.multilingual import MultilingualModel

from dataclasses import dataclass

from tools.patient_tools import (
    find_patient_by_name_tool,
    find_patient_by_phone_tool,
    register_patient_tool,
)

from tools.appointment_tools import (
    create_appointment_tool,
    get_available_doctors,
    get_patient_appointments_tool,
    cancel_appointment_tool,
    reschedule_appointment_tool,
)


logger = logging.getLogger(__name__)

load_dotenv()

@dataclass
class AppointmentData:
    patient_id: str = ""
    patient_name: str = ""
    doctor_id: str = ""
    doctor_name: str = ""


class MedicalAppointmentAgent(Agent):
    def __init__(self):
        today_str = datetime.now().strftime("%A, %Y-%m-%d")  
        super().__init__(instructions=f"""
             You are a professional medical clinic receptionist. Always start by greeting the caller and asking how you can help. 
             Do not ask for their name or phone number until you understand the reason for the call. Speak warmly, naturally, and professionally—never sound like an AI or mention tools.
             Today is {today_str}. Resolve relative dates (tomorrow, next Monday, etc.) to the correct future YYYY-MM-DD date. Never use a past date.

### Booking

* Always call `get_available_doctors` before discussing doctors. Never invent doctors, availability, or appointment details. Only use exact names returned by the tool.
* If no doctors are returned, say no doctors are available.
* Determine the needed specialist/doctor, then help the caller choose a doctor, date, and time.
* Collect personal information only after the doctor, date, and time are chosen.
* Ask: "Great. To complete your booking, may I have your full name?"
* Then: "Thank you. Could I have your mobile number?"
* Use the name and phone to find the patient.
* If found, tell the caller you found their record and continue.
* If not found, say: "I couldn't find an existing patient record. I'll register you first."
* Ask only: "May I have your date of birth?"
* Register using full name, mobile number, and DOB only. Do not ask for gender or email.
* After registration, immediately continue booking.
* Only confirm a booking when the booking tool returns `success=true`.
* If booking fails because the time is booked, clearly say the time is already booked and ask for another time.
* If the tool gives a specific error, tell the caller that message naturally. Never call a specific booking error a "technical issue."

### Cancellation

* First verify the patient using name and phone number.
* Then call `get_my_appointments` and use only returned appointment details.
* If none, say they have no booked appointments.
* If one, confirm it with the caller.
* If multiple, ask which appointment they want to cancel.
* Use `cancel_my_appointment` with the correct appointment ID.
* Confirm cancellation only when `success=true`; otherwise give the tool's actual error message.

### Rescheduling

* First verify the patient using name and phone number.
* Call `get_my_appointments`.
* If none, say they have no booked appointments.
* If one, confirm it; if multiple, ask which appointment to reschedule.
* Ask for the new date and time and convert relative dates to YYYY-MM-DD.
* Use `reschedule_my_appointment` with the correct appointment ID.
* If the time is booked, say it is already booked and ask for another time.
* If the doctor is unavailable, say so and ask for another time.
* Confirm rescheduling only when `success=true`; otherwise give the tool's actual error message.

### General rules

* Never invent doctors, slots, patient information, appointments, or tool results.
* Never claim a booking, cancellation, or reschedule succeeded unless the corresponding tool returns `success=true`.
* Never expose tool execution or internal processes.
* Always sound like a warm, patient, professional clinic receptionist.

            """)



    @function_tool()
    async def find_patient(self, context: RunContext, name: str):
        """
        Find a patient by name.
        """

        result = await find_patient_by_name_tool(context, name)
        if result["found"]:
            patient = result["patient"]

            context.userdata.patient_id = patient["id"]
            context.userdata.patient_name = patient["fullName"]
        return result



    @function_tool()
    async def find_patient_by_phone(self, context: RunContext, phone: str):
        """
        Find a patient by phone number.
        """

        result = await find_patient_by_phone_tool(context, phone)
        if result["found"]:
            patient = result["patient"]

            context.userdata.patient_id = patient["id"]
            context.userdata.patient_name = patient["fullName"]
        return result


    @function_tool()
    async def register_patient(self,context: RunContext,name: str,phone: str,dob: str):
        """
        Register a new patient.
        """
        print("========== REGISTER PATIENT TOOL ==========")
        print("NAME:", name)
        print("PHONE:", phone)
        print("DOB:", dob)

        result = await register_patient_tool(context=context,name=name,phone=phone,dob=dob,)

        print("REGISTER RESPONSE:")
        print(result)

        if result["success"]:
            patient_response = result["patient"]

            # Payload returns the created patient inside "doc"
            patient = patient_response["doc"]

            context.userdata.patient_id = patient["id"]
            context.userdata.patient_name = patient["fullName"]

            print("NEW PATIENT ID:", context.userdata.patient_id)

        return result



    @function_tool()
    async def get_available_doctors(self, context: RunContext):
        """
        Get a list of available doctors.
        """

        doctors = await get_available_doctors(context)
        print("DATABASE DOCTORS:", doctors)

        return doctors



    @function_tool()
    async def select_doctor(
        self,
        context: RunContext,
        doctor_name: str,
    ):
        """
        Save the selected doctor for the current conversation.
        """

        doctors = await get_available_doctors(context)

        print("DOCTORS FROM API:", doctors)

        for doctor in doctors["doctors"]:

            if doctor_name.lower() in doctor["name"].lower():

                context.userdata.doctor_id = doctor["id"]
                context.userdata.doctor_name = doctor["name"]

                return {"success": True, "doctor": doctor}

        return {"success": False, "message": "Doctor not found."}



    @function_tool()
    async def book_patient_appointment(
        self, context: RunContext, date: str,time: str, notes: Optional[str] = None
    ):
        """
        Book the appointment using the previously selected doctor.
        date must be an ISO date in YYYY-MM-DD format (e.g. "2026-08-12").
        time must be in 24-hour HH:MM format (e.g. "17:00").        
        """

        patient_id = context.userdata.patient_id
        doctor_id = context.userdata.doctor_id

        if not patient_id:
            return {"success": False, "message": "Patient not verified"}

        if not doctor_id:
            return {"success": False, "message": "Doctor not selected"}

        result = await create_appointment_tool(patient_id, doctor_id, date, time, notes)

        return result


    @function_tool()
    async def get_my_appointments(self, context: RunContext,):
        """
        Get the patient's current booked appointments.
        """

        patient_id = context.userdata.patient_id

        if not patient_id:
            return {
                "success": False,
                "message": "Patient not verified."
            }

        result = await get_patient_appointments_tool(
            patient_id
            )

        print("PATIENT APPOINTMENTS:", result)

        return result

    @function_tool()
    async def cancel_my_appointment( self,context: RunContext,appointment_id: str,):
        """
        Cancel a patient's appointment.
        """

        patient_id = context.userdata.patient_id

        if not patient_id:
            return {
                 "success": False,
                 "message": "Patient not verified."
            }

        result = await cancel_appointment_tool(
            appointment_id
        )

        print("CANCEL APPOINTMENT RESULT:", result)

        return result


    @function_tool()
    async def reschedule_my_appointment(self,context: RunContext,appointment_id: str,date: str,time: str,):
        """
        Reschedule an existing appointment.
        date must be YYYY-MM-DD.
        time must be HH:MM in 24-hour format.
        """

        patient_id = context.userdata.patient_id

        if not patient_id:
            return {
                "success": False,
                "message": "Patient not verified."
            }

        result = await reschedule_appointment_tool(appointment_id,date,time,)

        print("RESCHEDULE APPOINTMENT RESULT:", result)

        return result


    async def on_enter(self):
     await self.session.generate_reply(
        instructions="""
        Greet the caller.
        Introduce yourself naturally.
        Wait before asking personal information.
        """
     )


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):

    session = AgentSession(
        userdata=AppointmentData(),

        llm=llm.FallbackAdapter(
          [
            inference.LLM(model="openai/gpt-4.1-mini"),
            inference.LLM(model="google/gemini-2.5-flash"),
          ]
        ),

        stt=stt.FallbackAdapter(
          [
            inference.STT.from_model_string("assemblyai/universal-streaming:en"),
            inference.STT.from_model_string("deepgram/nova-3"),
          ]
        ),

        tts=tts.FallbackAdapter(
          [
            inference.TTS.from_model_string("cartesia/sonic-3:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
            inference.TTS.from_model_string("inworld/inworld-tts-1"),
          ]
        ),

        vad=silero.VAD.load(),

        turn_detection=MultilingualModel(),

        preemptive_generation=True,

    )


    usage_collector = metrics.UsageCollector()

    # Store the most recent End Of Utterance (EOU) metrics
    last_eou_metrics = None


    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):

        nonlocal last_eou_metrics

        if ev.metrics.type == "eou_metrics":
            last_eou_metrics = ev.metrics

        metrics.log_metrics(ev.metrics)

        usage_collector.collect(ev.metrics)



    async def log_usage():

        summary = usage_collector.get_summary()

        logger.info(
            "Usage summary: %s",
            summary
        )


    ctx.add_shutdown_callback(log_usage)



    @session.on("agent_state_changed")
    def _on_agent_state_changed(ev: AgentStateChangedEvent):

        if ev.new_state == "speaking":

            if last_eou_metrics:

                elapsed = (
                    time.time()
                    -
                    last_eou_metrics.timestamp
                )

                logger.info(
                    f"Time to first audio: {elapsed:.3f}s"
                )



    await session.start(

        agent=MedicalAppointmentAgent(),

        room=ctx.room,

        room_options=room_io.RoomOptions(

            audio_input=room_io.AudioInputOptions(

                noise_cancellation=noise_cancellation.BVC()

            ),

        ),

    )



if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO
    )

    agents.cli.run_app(server)