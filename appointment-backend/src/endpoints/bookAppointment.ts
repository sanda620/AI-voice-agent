import type { Endpoint } from 'payload'

export const bookAppointment: Endpoint = {

    path: '/book-appointment',

    method: 'post',


    handler: async (req) => {


        const body = await req.json?.()

        if (!body) {
            return Response.json(
                {
                    error: "Request body is required"
                },
                {
                    status: 400
                }
            )
        }



        const {

            patientPhone,

            doctorId,

            date

        } = body



        // Find patient
        const patients =
            await req.payload.find({

                collection: 'patients',

                where: {

                    phone: {

                        equals: patientPhone

                    }

                }

            })



        if (!patients.docs.length) {

            return Response.json({

                error: "Patient not found"

            }, {
                status: 404
            })

        }

        const patient =
            patients.docs[0]



        // Create appointment
        const appointment =
            await req.payload.create({

                collection: 'appointments',

                data: {

                    patient: patient.id,

                    doctor: doctorId,

                    date,

                    status: 'booked'

                }

            })



        return Response.json({

            success: true,

            appointmentId:
                appointment.id

        })


    }

}