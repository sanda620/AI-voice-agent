import type { CollectionConfig } from 'payload'

export const Patients: CollectionConfig = {
  slug: 'patients',

  access: {
    read: () => true,
  },

  admin: {
    useAsTitle: 'fullName',
  },

  fields: [
    {
      name: 'fullName',
      type: 'text',
      required: true,
    },

    {
      name: 'phone',
      type: 'text',
      required: true,
       unique:true,
    },

    {
      name: 'email',
      type: 'email',
      required: false,
    },

    {
      name: 'dateOfBirth',
      type: 'date',
      required: false,
    },

    {
      name: 'gender',
      type: 'select',
      required: false,
      options: [
        { label: 'Male', value: 'male' },
        { label: 'Female', value: 'female' },
        { label: 'Other', value: 'other' },
      ],
    },
  ],
}