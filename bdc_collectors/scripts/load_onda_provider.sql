INSERT INTO bdc.providers (name, description, uri, credentials)
     VALUES ('ONDA', 'ONDA DIAS provides free and open access to geospatial data and information, including full availability of Copernicus data.',
             'https://catalogue.onda-dias.eu/catalogue/',
             '{"username": "user@email.com", "password": "password"}')
         ON CONFLICT DO NOTHING;