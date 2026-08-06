import datetime
import logging

from dotenv import load_dotenv
from datetime import datetime
from typing import Optional
from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, JobContext, room_io
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.agents import llm, stt, tts, inference
from livekit.agents import AgentStateChangedEvent, MetricsCollectedEvent, metrics
from livekit.agents import mcp
import time
import httpx

from livekit.agents.beta.workflows import TaskGroup
from livekit.agents import AgentTask, function_tool, RunContext
from dataclasses import dataclass

from tools.patient_tools import find_patient_by_name_tool, find_patient_by_phone_tool
from tools.appointment_tools import create_appointment_tool, get_available_doctors

logger = logging.getLogger(__name__)
load_dotenv()


# Define result types for each task
@dataclass
class AppointmentData:
    patient_id: str = ""
    patient_name: str = ""
    doctor_id: str = ""
    doctor_name: str = ""


class MedicalAppointmentAgent(Agent):
    def __init__(self):
        today_str = datetime.now().strftime("%A, %Y-%m-%d")  
        super().__init__(instructions="""
             You are the a Medical help assistant.
             Your job is to conduct conversations exactly like a professional clinic receptionist.
             Always begin by greeting the caller and asking how you can help.
             Never ask for the caller's name or phone number at the beginning of the conversation.
             First understand why the caller is contacting the clinic.

             Today's date is {today_str}. Use this to correctly resolve any relative dates
             the caller mentions, such as "next Wednesday" or "tomorrow" — always compute
             the actual calendar date based on today, and never pick a date in the past.


             If the caller wants to book an appointment:
                • Determine the required specialist or doctor.
                • Help the caller choose a doctor.
                • Help the caller choose a date.
                • Help the caller choose an available time.

             Only after the caller has chosen a doctor, date and time should you collect personal information.

             Ask naturally:
             "Great. To complete your booking, may I have your full name?"
             After receiving the name:
             "Thank you. Could I have your mobile number?"
             Use the name and phone number to look up the patient.

             If the patient exists:
             Tell the caller you found their record and continue with the booking.

             If the patient does not exist:
             Say:
             "I couldn't find an existing patient record. I'll register you first."
             Then ask only:
             "May I have your date of birth?"

             Register the patient using:
                • full name
                • mobile number
                • date of birth

             Do not ask for gender.
             Do not ask for email.

             After registration, immediately continue with the appointment booking.
             Always sound warm, patient and professional.
             Never sound like an AI assistant.

             Avoid saying things like:
               "Executing tool..."
               "Patient lookup..."
               "Registration successful."

             Instead, speak naturally like a real receptionist.
            """)



    @function_tool()
    async def find_patient(self, context: RunContext, name: str):
        """
        Find a patient using their name.
        Use this when the patient provides their full name.
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
        Find a patient using their phone number.
        Use this only when name search fails.
        """

        result = await find_patient_by_phone_tool(context, phone)
        if result["found"]:
            patient = result["patient"]

            context.userdata.patient_id = patient["id"]
            context.userdata.patient_name = patient["fullName"]
        return result



    @function_tool()
    async def get_available_doctors(self, context: RunContext):
        """
        Get a list of available doctors.
        Use this to provide options for the patient to choose from.
        """

        doctors = await get_available_doctors(context)
        return doctors



    @function_tool()
    async def select_doctor(
        self,
        context: RunContext,
        doctor_name: str,
    ):
        """
        Save the selected doctor for the current conversation.
        Use this after the patient chooses a doctor.
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



    async def on_enter(self):
     await self.session.generate_reply(
        instructions="""
        Greet the caller warmly as a medical help assistant.
        Introduce yourself naturally.
        Ask only:
        "How may I help you today?"
        Do not ask for the caller's name.
        Wait for the caller to explain why they are calling before asking any personal information.
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
                inference.TTS.from_model_string(
                    "cartesia/sonic-3:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
                ),
                inference.TTS.from_model_string("inworld/inworld-tts-1"),
            ]
        ),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
        preemptive_generation=True,
        mcp_servers=[
            mcp.MCPServerHTTP(url="https://docs.livekit.io/mcp"),
        ],
    )

    usage_collector = metrics.UsageCollector()

    # Store the most recent End Of Utterance (EOU) metrics
    last_eou_metrics = None

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        nonlocal last_eou_metrics

        # Save the latest EOU metrics
        if ev.metrics.type == "eou_metrics":
            last_eou_metrics = ev.metrics

        # Log every metric and collect usage statistics
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():

        summary = usage_collector.get_summary()
        logger.info("Usage summary: %s", summary)

    ctx.add_shutdown_callback(log_usage)

    @session.on("agent_state_changed")
    def _on_agent_state_changed(ev: AgentStateChangedEvent):
        if ev.new_state == "speaking":
            if last_eou_metrics:
                # Calculate time since user finished speaking
                elapsed = time.time() - last_eou_metrics.timestamp
                logger.info(f"Time to first audio: {elapsed:.3f}s")

    await session.start(
        agent=MedicalAppointmentAgent(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            ),
        ),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    agents.cli.run_app(server)
