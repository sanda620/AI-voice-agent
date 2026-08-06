import type { CollectionConfig } from 'payload'

export const Doctors: CollectionConfig = {
  slug: 'doctors',

  access: {
    read: () => true,
  },

  admin: {
    useAsTitle: 'name',
  },

  fields: [
    {
      name: 'name',
      type: 'text',
      required: true,
    },

    {
      name: 'specialization',
      type: 'select',
      required: true,
      options: [
        { label: 'Cardiologist', value: 'cardiologist' },
        { label: 'Dermatologist', value: 'dermatologist' },
        { label: 'Neurologist', value: 'neurologist' },
        { label: 'Orthopedic', value: 'orthopedic' },
        { label: 'Pediatrician', value: 'pediatrician' },
        { label: 'General Physician', value: 'general_physician' },
      ],
    },

    {
      name: 'phone',
      type: 'text',
      required: true,
    },

    {
      name: 'email',
      type: 'email',
      required: true,
      unique: true,
    },

    {
      name: "availability",
      type: "array",
      fields: [
        {
          name: "day",
          type: "select",
          required: true,
          options: [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday"
          ],
        },
        {
          name: "startTime",
          type: "text",
          required: true,
          admin: {
            placeholder: "Example: 09:00"
          }
        },
        {
          name: "endTime",
          type: "text",
          required: true,
          admin: {
            placeholder: "Example: 17:00"
          }
        }
      ]
    },
  ],
}