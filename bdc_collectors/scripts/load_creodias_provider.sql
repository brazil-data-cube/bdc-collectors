INSERT INTO bdc.providers (name, description, uri, credentials)
     VALUES ('CREODIAS', 'CREODIAS is a seamless environment that brings processing to Earth Observation data (EODATA - EO DATA Free Archive) . Our platform contains online most of Copernicus Sentinel satellites data and Services, Envisat and ESA/Landsat data and other EODATA. Its design allows Third Party Users to prototype and build their own value-added services and products.',
             'https://creodias.eu/what-is-creodias',
             '{"username": "user@email.com", "password": "password"}')
         ON CONFLICT DO NOTHING;