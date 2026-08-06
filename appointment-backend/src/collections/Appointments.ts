import type { CollectionConfig } from 'payload'
import { APIError } from 'payload'

export const Appointments: CollectionConfig = {
  slug: 'appointments',

  access: {
    create: () => true,
    read: () => true,
    update: () => true,
    delete: () => true,
  },

  admin: {
    useAsTitle: 'id',
  },

  hooks: {
    beforeValidate: [
      async ({ data, req }) => {


        if (!data) {
          return data
        }


        // Skip validation when updating status only
        if (
          data.status === 'cancelled' ||
          data.status === 'completed'
        ) {
          return data
        }


        if (!data?.doctor || !data?.date) {
          return data
        }


        //Get Doctor
        const doctor = await req.payload.findByID({
          collection: 'doctors',
          id:
            typeof data.doctor === 'object'
              ? data.doctor.id
              : data.doctor,
        })


        if (!doctor) {
          throw new Error('Doctor not found')
        }


        const appointmentDate = new Date(data.date)

        // Reject any appointment date/time that has already passed
       if (appointmentDate.getTime() < Date.now()) {
          throw new APIError(
             'Cannot book an appointment in the past. Please select a future date and time.',
              400
          )
        }

        const day = appointmentDate.toLocaleDateString(
          'en-US',
          {
            weekday: 'long',
          }
        )


        const selectedTime = appointmentDate
          .toLocaleTimeString(
            'en-GB',
            {
              hour: '2-digit',
              minute: '2-digit',
              hour12: false,
            }
          )


        // Check Doctor Availability
        const isAvailable = doctor.availability?.some(
          (slot: any) => {

            const startTime = slot.startTime.replace('.', ':')
            const endTime = slot.endTime.replace('.', ':')


            return (
              slot.day === day &&
              selectedTime >= startTime &&
              selectedTime <= endTime
            )
          }
        )


        if (!isAvailable) {
          throw new APIError(
            `Doctor is unavailable on ${day} at ${selectedTime}. Please select another time.`,
            400
          )
        }


        // Check existing appointment
        const existingAppointments = await req.payload.find({
          collection: 'appointments',
          where: {
            and: [
              {
                doctor: {
                  equals:
                    typeof data.doctor === 'object'
                      ? data.doctor.id
                      : data.doctor,
                },
              },
              {
                date: {
                  equals: data.date,
                },
              },
              {
                status: {
                  not_equals: 'cancelled',
                },
              },
            ],
          },
        })


        if (existingAppointments.docs.length > 0) {

          throw new APIError(
            'This doctor already has an appointment at this time.',
            400
          )

        }


        return data
      },
    ],
  },


  fields: [

    {
      name: 'patient',
      type: 'relationship',
      relationTo: 'patients',
      required: true,
    },


    {
      name: 'doctor',
      type: 'relationship',
      relationTo: 'doctors',
      required: true,
    },


    {
      name: 'date',
      type: 'date',
      required: true,

      admin: {
        date: {
          pickerAppearance: 'dayAndTime',
        },
      },
    },


    {
      name: 'status',
      type: 'select',
      required: true,
      defaultValue: 'booked',
      options: [
        {
          label: 'Booked',
          value: 'booked',
        },
        {
          label: 'Cancelled',
          value: 'cancelled',
        },
        {
          label: 'Completed',
          value: 'completed',
        },
      ],
    },


    {
      name: 'notes',
      type: 'textarea',
      required: false,
    },

  ],
}