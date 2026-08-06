import type { Endpoint } from 'payload'


export const findPatient: Endpoint = {

  path: '/find-patient',

  method: 'get',

  handler: async (req) => {

    const phone = req.query.phone as string
    const name = req.query.name as string


    if (!phone && !name) {

      return Response.json(
        {
          error: "Please provide phone or name"
        },
        {
          status: 400
        }
      )

    }


    let where:any = {}


    // Search by phone first
    if (phone) {

      where = {
        phone: {
          equals: phone
        }
      }

    }


    // Search by name if phone not provided
    else if (name) {

      where = {
        fullName: {
          contains: name
        }
      }

    }



    const patients =
      await req.payload.find({

        collection: 'patients',

        where

      })



    if (patients.docs.length === 0) {

      return Response.json(
        {
          found: false,
          message: "Patient not found"
        },
        {
          status:404
        }
      )

    }



    return Response.json({

      found:true,

      patients: patients.docs.map(
        patient => ({
          
          id: patient.id,

          fullName: patient.fullName,

          phone: patient.phone,

          email: patient.email

        })
      )

    })


  }

}