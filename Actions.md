
#notes:
    pip install mysqlclient # the other drivers don't work well


#authorization
    in settings.py auth_user_model is set to customuser, so standard functions such as get_user_model, create_user, etc. work
    
## start
    cd /Users/mo/GoogleDrive/dev/planetdestin1/beach_rental_site
    . ../../env/bin/activate
    python manage.py runserver

# user management

    1. Get all the links working (login back to reservation) DONE
    2. add hthe property number to the unit information (VRBO CSV download uses it) Done
    3. add a GUI to import the csv's (should be able do one or more) DONE
    
    4. Phone numbers are not properly formatted when added to users from spreadsheet
    5. if a user exists but has no password, then offer to send them email with the password DONE
    6. Handle the phone number situation (created from spreadsheet may not match the user, but key on email ) DONE
    7. if phone is different from vrbo, then save it as a secondary phone?  TODO
    8. Reset emails sent to me right now, change it later to the customer

    4. Add a report that says pull is needed (no email since also does it regularly)
    5. if the user is created through spreadsheet, then send them an email (if they have one)
        with a tmp password and let them know (have a field that says new user); if they didn't have
        an email or need to get in, add a button to send an email

# PRODUCTION CHECKLIST
    1. Set SESSION_COOKIE_SECURE to true in settings.py

   

    User app tutorial : https://www.youtube.com/watch?v=hN0xbn4sENw&t=2s
    python manage.py startapp users


    


- Later:
    - move pull vrbo to an admin role
    - Add admin to do a timely pull also

# Extract user information from VRBO (or ali)

# allow submission of reservation only
    2. just submit and save as inquiry

# user area

# load into Hostinger