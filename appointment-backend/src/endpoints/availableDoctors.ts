import type { Endpoint } from 'payload'

export const availableDoctors: Endpoint = {

  path: '/available-doctors',

  method: 'get',

  handler: async (req) => {

    const specialization =
      req.query.specialization


    const doctors = await req.payload.find({
      collection: 'doctors',

      where: specialization
        ? {
            specialization: {
              equals: specialization,
            },
          }
        : {},
    })


    return Response.json({
      doctors: doctors.docs,
    })

  },

}