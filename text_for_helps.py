common_part = """
This bot allows you to book table in a restaurant. 
There are the following command allowed to use:

/getid - get id of the chat
/exit - to exit from booking process

/booktable - to book a table for specific date (e.g. in the future or today)
/booktabletoday - to book a table for today only

NOTE. you need a table number for these commands
/cancelreservation - to cancel reservation for a table (for any date). 
/cancelreservationtoday- to cancel reservation for a table for today only.
"""

customer_help = f"""
{common_part}

/mybookings - to check all your bookings

/customerrequest - to request send a request to manager directly, simple message
"""

manager_help = f"""
{common_part}

/checkbookings - check all bookings for specific date
/checkbookingstoday - to check all bookings for today
/allbookings - to check all bookings for all dates

/bookbynumber - to book a table by number for today only
/forcebooking - to book a table for for today by number without name and time

/backupreservations - to backup all reservations to file
"""