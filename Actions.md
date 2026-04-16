
#notes:
    pip install mysqlclient # the other drivers don't work well


#authorization
    in settings.py auth_user_model is set to customuser, so standard functions such as get_user_model, create_user, etc. work
    
## start
    cd /Users/mo/GoogleDrive/dev/planetdestin1/beach_rental_site
    . ../../env/bin/activate
    python manage.py runserver

# finish showing free units 
    1. show available units - DONE
    1.4 Checkout date is one before - DONE
    1.5 add additional info about each unit - DONE
    1.55 add pictures and stuff to the additional info  DONE
    1.6 inquiry creates inquiry but mesasge is not green; also change it so you get out of that page; also if user make multiple inquiries, only keep the last one DONE

# complete the registration page
    0. create a repository DONE
    1. color is black, turn it light DONE
    4. turn the user back to the registration (if they came from there)
    5. Send an email with the renter request

## created a new user app
    tutorial: https://www.youtube.com/watch?v=hN0xbn4sENw&t=2s
    python manage.py startapp users


    


- Later:
    - move pull vrbo to an admin role
    - Add admin to do a timely pull also

# Extract user information from VRBO (or ali)

# allow submission of reservation only
    2. just submit and save as inquiry

# user area

# load into Hostinger