import type { Endpoint } from 'payload'

export const checkAvailability: Endpoint = {

  path: '/check-availability',

  method: 'get',

  handler: async (req) => {


    const doctorId =
      req.query.doctorId as string


    const date =
      req.query.date as string



    if (!doctorId || !date) {

      return Response.json(
        {
          error:
          "doctorId and date are required"
        },
        {
          status:400
        }
      )

    }



    const doctor =
      await req.payload.findByID({

        collection:'doctors',

        id:doctorId

      })



    const selectedDate =
      new Date(date)



    const day =
      selectedDate.toLocaleDateString(
        'en-US',
        {
          weekday:'long'
        }
      )



    const availability =
      doctor.availability?.find(
        (slot:any)=>
          slot.day === day
      )



    if(!availability){

      return Response.json({

        availableSlots:[]

      })

    }



    const slots:string[] = []


    let start =
      availability.startTime.replace(
        '.',
        ':'
      )


    const end =
      availability.endTime.replace(
        '.',
        ':'
      )



    while(start < end){

      slots.push(start)


      let [hour,minute] =
        start.split(':')
          .map(Number)


      minute += 30


      if(minute >= 60){

        hour++
        minute -= 60

      }


      start =
        `${hour
          .toString()
          .padStart(2,'0')}:${minute
          .toString()
          .padStart(2,'0')}`

    }



    return Response.json({

      doctor:doctor.name,

      date,

      availableSlots:slots

    })


  }

}