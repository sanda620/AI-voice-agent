import type { Endpoint } from 'payload'
import { APIError } from 'payload'


export const cancelAppointment: Endpoint = {

  path: '/cancel-appointment',

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
      appointmentId
    } = body



    if (!appointmentId) {

      throw new APIError(
        'Appointment ID required',
        400
      )

    }



    const appointment =
      await req.payload.findByID({

        collection:'appointments',

        id: appointmentId

      })



    if (!appointment) {

      throw new APIError(
        'Appointment not found',
        404
      )

    }



    const updatedAppointment =
      await req.payload.update({

        collection:'appointments',

        id:appointmentId,

        data:{
          status:'cancelled'
        }

      })



    return Response.json({

      success:true,

      message:
      "Appointment cancelled successfully",

      appointmentId:
      updatedAppointment.id

    })


  }

}