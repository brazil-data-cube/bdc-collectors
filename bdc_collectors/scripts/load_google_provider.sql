INSERT INTO bdc.providers (name, description, uri, credentials)
     VALUES ('Google', 'Google Cloud Storage of Public data sets - Landsat and Sentinel',
             'https://cloud.google.com/storage/docs/public-datasets',
             '{"GOOGLE_APPLICATION_CREDENTIALS": ""}')
         ON CONFLICT DO NOTHING;