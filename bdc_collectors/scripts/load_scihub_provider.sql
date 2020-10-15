INSERT INTO bdc.providers (name, description, uri, credentials)
     VALUES ('SciHub', '',
             'https://scihub.copernicus.eu/dhus',
             '{"username": "user@email.com", "password": "password"}')
         ON CONFLICT DO NOTHING;