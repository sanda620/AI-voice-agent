import type { Endpoint } from 'payload'


export const myAppointments: Endpoint = {

  path: '/my-appointments',

  method: 'get',

  handler: async (req) => {


    const phone = req.query.phone as string


    if (!phone) {

      return Response.json(
        {
          error: "Phone number is required"
        },
        {
          status: 400
        }
      )

    }



    // Find patient

    const patients =
      await req.payload.find({

        collection: 'patients',

        where: {
          phone: {
            equals: phone
          }
        }

      })



    if (patients.docs.length === 0) {

      return Response.json(
        {
          error: "Patient not found"
        },
        {
          status: 404
        }
      )

    }



    const patient =
      patients.docs[0]



    // Find appointments

    const appointments =
      await req.payload.find({

        collection: 'appointments',

        where: {

          patient: {

            equals: patient.id

          }

        },

        sort: '-date'

      })



    return Response.json({

      patient: {

        id: patient.id,

        name: patient.fullName,

        phone: patient.phone

      },


      appointments:
        appointments.docs.map(
          (appointment:any) => ({


            id: appointment.id,


            doctor:
              typeof appointment.doctor === 'object'
                ? appointment.doctor.name
                : appointment.doctor,


            specialization:
              typeof appointment.doctor === 'object'
                ? appointment.doctor.specialization
                : null,


            date: appointment.date,


            status: appointment.status,


            notes: appointment.notes || null


          })

        )

    })


  }

}