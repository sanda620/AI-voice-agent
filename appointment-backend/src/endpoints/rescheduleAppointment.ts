import type { Endpoint } from 'payload'
import { APIError } from 'payload'


export const rescheduleAppointment: Endpoint = {

  path: '/reschedule-appointment',

  method: 'post',

  handler: async (req) => {


    const body = await req.json?.()


    if (!body) {
      throw new APIError(
        'Request body required',
        400
      )
    }


    const {
      appointmentId,
      newDate
    } = body



    if (!appointmentId || !newDate) {

      throw new APIError(
        'appointmentId and newDate are required',
        400
      )

    }



    // Get existing appointment

    const appointment =
      await req.payload.findByID({

        collection: 'appointments',

        id: appointmentId

      })



    if (!appointment) {

      throw new APIError(
        'Appointment not found',
        404
      )

    }



    // Get doctor

    const doctor =
      await req.payload.findByID({

        collection:'doctors',

        id:
          typeof appointment.doctor === 'object'
          ? appointment.doctor.id
          : appointment.doctor

      })



    if (!doctor) {

      throw new APIError(
        'Doctor not found',
        404
      )

    }



    // Check day and time

    const appointmentDate =
      new Date(newDate)



    const day =
      appointmentDate.toLocaleDateString(
        'en-US',
        {
          weekday:'long'
        }
      )



    const selectedTime =
      appointmentDate.toLocaleTimeString(
        'en-GB',
        {
          hour:'2-digit',
          minute:'2-digit',
          hour12:false
        }
      )



    // Check doctor availability

    const isAvailable =
      doctor.availability?.some(
        (slot:any)=>{


          const startTime =
            slot.startTime.replace('.', ':')


          const endTime =
            slot.endTime.replace('.', ':')



          return (
            slot.day === day &&
            selectedTime >= startTime &&
            selectedTime <= endTime
          )

        }
      )



    if(!isAvailable){

      throw new APIError(
        `Doctor is unavailable on ${day} at ${selectedTime}`,
        400
      )

    }




    // Check double booking

    const existingAppointments =
      await req.payload.find({

        collection:'appointments',

        where:{

          and:[

            {
              doctor:{
                equals:
                typeof appointment.doctor === 'object'
                ? appointment.doctor.id
                : appointment.doctor
              }
            },


            {
              date:{
                equals:newDate
              }
            },


            {
              status:{
                not_equals:'cancelled'
              }
            },


            {
              id:{
                not_equals:appointmentId
              }
            }

          ]

        }

      })



    if(existingAppointments.docs.length > 0){

      throw new APIError(
        'This doctor already has an appointment at this time.',
        400
      )

    }




    // Update appointment

    const updatedAppointment =
      await req.payload.update({

        collection:'appointments',

        id:appointmentId,

        data:{

          date:newDate,

          status:'booked'

        }

      })



    return Response.json({

      success:true,

      message:
      'Appointment rescheduled successfully',

      appointmentId:
      updatedAppointment.id

    })


  }

}