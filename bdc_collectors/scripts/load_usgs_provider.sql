INSERT INTO bdc.providers (name, description, uri, credentials)
     VALUES ('USGS', 'The USGS Earth Explorer data portal is your one stop shop for obtaining geo-spatial datasets from our extensive collections',
             'https://earthexplorer.usgs.gov/',
             '{"username": "user@email.com", "password": "password"}')
         ON CONFLICT DO NOTHING;