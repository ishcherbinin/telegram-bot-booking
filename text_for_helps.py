common_part = """
This bot allows you to book table in a restaurant. 
There are the following command allowed to use:

/booktable - to book a table for specific date (e.g. in the future or today)
/booktabletoday - to book a table for today only

NOTE. you need a table number for these commands
/cancelreservation - to cancel reservation for a table (for any date). 
/cancelreservationtoday- to cancel reservation for a table for today only.
"""

customer_help = common_part

manager_help = f"""
{common_part}

/checkbookings - check all bookings for specific date
/checkbookingstoday - to check all bookings for today

/getid - get id of the chat

"""