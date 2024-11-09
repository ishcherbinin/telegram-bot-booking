import asyncio
import logging.config
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from faker import Faker
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from logging_conf import log_config
from restaurant_space import TablesStorage, Table
from text_for_helps import customer_help, manager_help
from validators import validate_date, validate_time, validate_seats

logging.config.dictConfig(log_config)

_logger = logging.getLogger(__name__)

# assign environment variables to variables
api_token = os.getenv("TELEGRAM_API_TOKEN")

group_chat_id = str(os.getenv("GROUP_CHAT_ID"))

dist_tables = Path(os.path.dirname(__file__)) / Path("tables_distribution") / Path(os.getenv("TABLES_FILE"))
allowed_chat_ids = {os.getenv("ALLOWED_CHAT_IDS")} | {group_chat_id}
backup_csv_file = Path(os.path.dirname(__file__)) / Path("./backup_tables.csv")

# create relevant objects
tables_storage = TablesStorage.from_csv_file(Path(dist_tables))

bot = Bot(token=api_token)
storage = MemoryStorage()
ds = Dispatcher(storage=storage)
faker = Faker()

booking_requests = {}


# Define the FSM states for each step
class OrderStates(StatesGroup):
    waiting_for_seats = State()
    waiting_for_date_client = State()
    waiting_for_name = State()
    waiting_for_time = State()
    waiting_for_confirmation = State()
    wait_for_number_for_cancel = State()
    waiting_cancel_reservation = State()
    waiting_for_request_message = State()
    waiting_for_date_for_availability = State()


class ManagerStates(StatesGroup):
    waiting_for_date_manager = State()
    waiting_for_table_number = State()
    waiting_for_table_number_force = State()


"""
Part with utility functions for bot
"""
async def print_table(table: Table, message: types.Message) -> None:
    await message.answer(f"\nDate: {table.readable_booking_date},"
                         f"\nTable №: {table.table_id},"
                         f"\nNumber of seats: {table.capacity},"
                         f"\nBooking time: {table.readable_booking_time},"
                         f"\nName: {table.user_name}")


async def get_requested_date(message: types.Message) -> Optional[datetime]:
    date = message.text
    chosen_date, text = await validate_date(date)
    if chosen_date is None:
        await message.answer(text)
        return
    return chosen_date


"""
This part defines common part which might be used by account or manager to book table or cancel reservation in the restaurant
Open chat with bot and type /book-table to start booking process
"""


@ds.message(Command(commands=["help", "start"]))
async def help_command(message: types.Message):
    _logger.info("Help command is requested")
    if await validate_chat_id(str(message.chat.id)):
        await message.answer(customer_help)
    else:
        await message.answer(manager_help)


@ds.message(Command("exit"))
async def exit_command(message: types.Message, state: FSMContext):
    _logger.info("Exit command is requested")
    await message.answer("You have exited the process")
    await state.clear()

@ds.message(Command("availabletables"))
async def available_tables(message: types.Message, state: FSMContext):
    _logger.info("Available tables command is requested")
    await message.answer("Please provide date you want to check availability for. Format: DD.MM")
    await state.set_state(OrderStates.waiting_for_date_for_availability)

@ds.message(Command("availabletablestoday"))
async def available_tables_today(message: types.Message, state: FSMContext):
    _logger.info("Available tables for today command is requested")
    chosen_date = datetime.now()
    tables_for_date = tables_storage.get_tables_for_date(chosen_date.date())
    free_tables = [table for table in tables_for_date if not table.is_reserved]
    if not free_tables:
        await message.answer("There are no available tables for today")
        return
    for table in free_tables:
        await message.answer(f"Available table for today: "
                             f"\nID: {table.table_id}"
                             f"\nNumber of seats: {table.capacity}")
    await state.clear()

@ds.message(OrderStates.waiting_for_date_for_availability)
async def process_date_for_availability(message: types.Message, state: FSMContext):
    _logger.info("Processing request particular date for checking availability")
    chosen_date = await get_requested_date(message)
    if chosen_date is None:
        await state.set_state(OrderStates.waiting_for_date_for_availability)
        return
    tables_for_date = tables_storage.get_tables_for_date(chosen_date.date())
    free_tables = [table for table in tables_for_date if not table.is_reserved]
    if not free_tables:
        await message.answer("There are no available tables for this date")
        await state.clear()
        return
    for table in free_tables:
        await message.answer(f"Available table for {chosen_date.date()}: "
                             f"\nID: {table.table_id}"
                             f"\nNumber of seats: {table.capacity}")
    await state.clear()


@ds.message(Command("booktable"))
async def book_table(message: types.Message, state: FSMContext):
    _logger.info("Start booking table")
    _logger.debug(message)
    await message.answer("Please provide date you want to reserve table for. Format: DD.MM")
    await state.set_state(OrderStates.waiting_for_date_client)


@ds.message(Command("booktabletoday"))
async def book_table_today(message: types.Message, state: FSMContext):
    _logger.info("Start booking table for today")
    await message.answer("Please provide number of seats you need")
    chosen_date = datetime.now()
    tables_for_date = tables_storage.get_tables_for_date(chosen_date.date())
    await state.set_data({"tables": tables_for_date, "date": chosen_date})
    await state.set_state(OrderStates.waiting_for_seats)


@ds.message(Command("mybookings"))
async def my_bookings(message: types.Message, state: FSMContext):
    _logger.info("Start checking bookings")
    if not await validate_chat_id(str(message.chat.id)):
        await message.answer("You are not allowed to use this command")
        return
    all_tables = tables_storage.get_all_tables
    no_bookings_found = True
    for date, bookings in all_tables.items():
        user_bookings = [table for table in bookings
                         if table.user_id == message.from_user.username and table.is_reserved]
        for booking in user_bookings:
            await print_table(booking, message)
            no_bookings_found = False
    if no_bookings_found:
        await message.answer("You have no bookings")
    await state.clear()


@ds.message(Command("customerrequest"))
async def customer_request(message: types.Message, state: FSMContext):
    _logger.info("Start customer request")
    await message.answer("Please provide your request")
    await state.set_state(OrderStates.waiting_for_request_message)


@ds.message(OrderStates.waiting_for_request_message)
async def process_request(message: types.Message, state: FSMContext):
    _logger.info("Processing customer request")
    request = message.text
    await bot.send_message(chat_id=group_chat_id,
                           text=f"Request from user '{message.from_user.username}': {request}")
    await message.answer("Your request is sent to manager")
    await state.clear()


@ds.message(OrderStates.waiting_for_date_client)
async def process_date(message: types.Message, state: FSMContext):
    _logger.info("Processing request particular date for booking")
    chosen_date = await get_requested_date(message)
    if chosen_date is None:
        await state.set_state(OrderStates.waiting_for_date_client)
        return
    tables_for_date: Tuple[Table, ...] = tables_storage.get_tables_for_date(chosen_date.date())
    await state.set_data({"tables": tables_for_date, "date": chosen_date})
    await message.answer("Please provide the number of seats you need")
    await state.set_state(OrderStates.waiting_for_seats)


@ds.message(OrderStates.waiting_for_seats)
async def process_seats(message: types.Message, state: FSMContext):
    _logger.info("Processing request for number of seats")
    seats = message.text
    seats = await validate_seats(seats)
    if seats is None:
        await message.answer("Please enter a valid number. Number should be digit")
        await state.set_state(OrderStates.waiting_for_seats)
        return
    _logger.info(f"User requested table for {seats} seats")
    data = await state.get_data()
    tables = data["tables"]
    table = tables_storage.search_for_table(seats, tables)
    if not table:
        await message.answer("Sorry, we don't have a table for this number of seats")
        await state.set_state(OrderStates.waiting_for_seats)
        return
    await state.update_data({"table": table})
    await message.answer("Please provide name you want to book the table for")
    await state.set_state(OrderStates.waiting_for_name)


@ds.message(OrderStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    _logger.info("Processing user name")
    name = message.text
    _logger.info(f"User name: {name}")
    data = await state.get_data()
    table = data["table"]
    table.user_name = name
    await message.answer("Please provide time you want to book the table for. Format: HH:MM")
    await message.answer("NOTE. Booking will be kept only for 1 hour after time you provided")
    await state.set_state(OrderStates.waiting_for_time)


@ds.message(OrderStates.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    _logger.info("Processing booking time")
    data = await state.get_data()
    time = message.text
    target_date = data["date"]
    booking_time, text = await validate_time(time, target_date)
    if booking_time is None:
        await message.answer(text)
        await state.set_state(OrderStates.waiting_for_time)
        return
    _logger.info(f"Booking time: {booking_time}")
    table = data["table"]
    table.booking_time = booking_time
    await message.answer(f"Table for {table.capacity} seats for "
                         f"{table.user_name} at {table.readable_booking_time}")
    await message.answer("Please confirm the booking. Answer Yes/No")
    await state.set_state(OrderStates.waiting_for_confirmation)


@ds.message(OrderStates.waiting_for_confirmation)
async def process_confirmation(message: types.Message, state: FSMContext):
    _logger.info("Processing confirmation from client")
    data = await state.get_data()
    table = data["table"]
    confirmation = message.text.upper()
    if confirmation == "YES":
        await message.answer(f"Table {table.table_id} for {table.capacity} "
                             f"seats is booked for {table.user_name} at {table.readable_booking_time}")
        validation = await validate_chat_id(str(message.chat.id))
        if validation:
            booking_requests[table.table_id] = {"chat_id": message.chat.id, "table": table}
            await message.answer("Wait till manager confirm your booking")
            await send_request_to_chat(message, table)
        else:
            table.is_reserved = True
            table.user_id = message.from_user.username
            await message.answer("Booking is confirmed")
    else:
        table.user_name = None
        table.booking_time = None
        await message.answer("Booking is rejected")
        await state.set_state(OrderStates.waiting_for_seats)
    await state.clear()


async def send_request_to_chat(message: types.Message, table: Table) -> None:
    _logger.info(f"Sending booking detail to separate chat {group_chat_id}")
    user = message.from_user.username
    table.user_id = user
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Confirm Booking", callback_data=f"confirm_")]
        ]
    )
    await bot.send_message(chat_id=group_chat_id,
                           text=f"\nUser name: {user} "
                                f"\nTable №: {table.table_id},"
                                f"\nNumber of seats: {table.capacity},"
                                f"\nBooking time: {table.readable_booking_time},"
                                f"\nName: {table.user_name}",
                           reply_markup=keyboard)


@ds.callback_query(lambda query: query.data.startswith("confirm_"))
async def confirm_booking(query: types.CallbackQuery):
    _logger.info("Manager confirmed booking")
    text = query.message.text
    match = re.search(r"Table №: (\d+)", text)
    table_id = int(match.group(1))
    table = booking_requests[table_id]["table"]
    table.is_reserved = True
    user_chat_id = booking_requests[table_id]["chat_id"]
    await bot.send_message(chat_id=user_chat_id,
                           text=f"Your booking is confirmed")
    await bot.send_message(chat_id=user_chat_id, text="See you soon!")
    await bot.send_message(chat_id=user_chat_id, text="To check your bookings use /mybookings")
    await bot.send_message(chat_id=group_chat_id, text=f"Booking for table №{table_id} is confirmed")
    booking_requests.pop(table_id)


@ds.message(Command("cancelreservation"))
async def cancel_reservation(message: types.Message, state: FSMContext):
    _logger.info("Start cancelling reservation")
    await message.answer("Please provide date you want to cancel reservation for. Format: DD.MM")
    await state.set_state(OrderStates.wait_for_number_for_cancel)


@ds.message(Command("cancelreservationtoday"))
async def cancel_reservation_today(message: types.Message, state: FSMContext):
    _logger.info("Start cancelling reservation for today")
    chosen_date = datetime.now()
    tables_for_date = tables_storage.get_tables_for_date(chosen_date.date())
    await state.set_data({"tables": tables_for_date})
    await message.answer("Please provide table number you want to cancel reservation for.")
    await state.set_state(OrderStates.waiting_cancel_reservation)


@ds.message(OrderStates.wait_for_number_for_cancel)
async def process_number_for_reservation_cancel(message: types.Message, state: FSMContext):
    _logger.info("Processing request for table number to cancel reservation")
    date = message.text
    chosen_date, text = await validate_date(date)
    if chosen_date is None:
        await message.answer(text)
        await state.set_state(OrderStates.wait_for_number_for_cancel)
        return
    tables_for_date = tables_storage.get_tables_for_date(chosen_date.date())
    tables = [table for table in tables_for_date if table.is_reserved]
    if not tables:
        await message.answer("There are no bookings for this date")
        await state.clear()
        return
    await message.answer(f"Please provide table number you want to cancel reservation for.")
    if not await validate_chat_id(str(message.chat.id)):
        await message.answer(f"Available tables: {[table.table_id for table in tables]}")
    await state.set_data({"tables": tables})
    await state.set_state(OrderStates.waiting_cancel_reservation)


@ds.message(OrderStates.waiting_cancel_reservation)
async def process_cancel_reservation(message: types.Message, state: FSMContext):
    _logger.info("Processing request for table number to cancel reservation")
    table_number = message.text
    user_id = message.from_user.username
    data = await state.get_data()
    tables = data["tables"]
    if await validate_chat_id(str(message.chat.id)):
        table = next((table for table in tables if table.table_id == int(table_number) and
                      table.user_id == user_id), None)
    else:
        table = next((table for table in tables if table.table_id == int(table_number) and
                      table.is_reserved), None)
    if table is None:
        await message.answer("Table with this number is not found or not reserved yet")
        await state.set_state(OrderStates.waiting_cancel_reservation)
        return
    table.is_reserved = False
    table.booking_time = None
    table.user_name = None
    table.user_id = None
    await message.answer(f"Reservation for table №{table.table_id} is cancelled")
    await state.clear()


"""
This part defines manager oriented part which might be used by manager to check bookings
"""


async def validate_chat_id(chat_id: str) -> bool:
    _logger.debug(f"Chat id: {chat_id}")
    _logger.debug(f"Allowed chat ids: {allowed_chat_ids}")
    if chat_id not in allowed_chat_ids:
        return True
    return False


@ds.message(Command("allbookings"))
async def all_bookings(message: types.Message, state: FSMContext):
    _logger.info("Start checking all bookings")
    if await validate_chat_id(str(message.chat.id)):
        await message.answer("You are not allowed to use this command")
        return
    all_booked_tables = tables_storage.get_all_tables
    for date, bookings in all_booked_tables.items():
        for table in bookings:
            if not table.is_reserved:
                continue
            await print_table(table, message)
    await state.clear()


@ds.message(Command("checkbookings"))
async def check_bookings(message: types.Message, state: FSMContext):
    _logger.info("Start checking bookings")
    if await validate_chat_id(str(message.chat.id)):
        await message.answer("You are not allowed to use this command")
        return
    await message.answer("Please provide date you want to check bookings for. Format: DD.MM")
    await state.set_state(ManagerStates.waiting_for_date_manager)


@ds.message(Command("checkbookingstoday"))
async def check_bookings_today(message: types.Message, state: FSMContext):
    _logger.info("Start checking bookings for today")
    if await validate_chat_id(str(message.chat.id)):
        await message.answer("You are not allowed to use this command")
        return
    chosen_date = datetime.now()
    tables_for_date = tables_storage.get_tables_for_date(chosen_date.date())
    tables = [table for table in tables_for_date if table.is_reserved]
    if not tables:
        await message.answer("There are no bookings for today")
        return
    for table in tables:
        await print_table(table, message)
    await state.clear()


@ds.message(ManagerStates.waiting_for_date_manager)
async def process_date_manager(message: types.Message, state: FSMContext):
    _logger.info("Processing request particular date for checking bookings")
    chosen_date = await get_requested_date(message)
    if chosen_date is None:
        await state.set_state(ManagerStates.waiting_for_date_manager)
        return
    tables_for_date = tables_storage.get_tables_for_date(chosen_date.date())
    tables = [table for table in tables_for_date if table.is_reserved]
    if not tables:
        await message.answer("There are no bookings for this date")
        await state.clear()
        return
    for table in tables:
        await print_table(table, message)
    await state.clear()


@ds.message(Command("getid"))
async def get_id(message: types.Message):
    ids = str(message.chat.id)
    _logger.info(f"Chat id: {ids}")
    await message.answer(ids)


@ds.message(Command("backupreservations"))
async def backup_reservations(message: types.Message):
    if str(message.chat.id) not in allowed_chat_ids:
        await message.answer("You are not allowed to use this command")
        return
    tables_storage.backup_to_csv_file(backup_csv_file)
    await message.answer("Backup is done")


@ds.message(Command("forcebooking"))
async def book_by_number(message: types.Message, state: FSMContext):
    _logger.info("Start booking table by number without name and time")
    if await validate_chat_id(str(message.chat.id)):
        await message.answer("You are not allowed to use this command")
        return
    await message.answer("Please provide table number you want to book")
    await state.set_state(ManagerStates.waiting_for_table_number_force)


@ds.message(ManagerStates.waiting_for_table_number_force)
async def process_table_number(message: types.Message, state: FSMContext):
    _logger.info("Processing request for table number to book by force")
    table_number = message.text
    chosen_date = datetime.now()
    tables = tables_storage.get_tables_for_date(chosen_date.date())
    table = next((table for table in tables if table.table_id == int(table_number)), None)
    if table is None:
        await message.answer("Table with this number is not found")
        await state.set_state(ManagerStates.waiting_for_table_number_force)
        return
    if table.is_reserved:
        await message.answer("Table is already reserved")
        await state.set_state(ManagerStates.waiting_for_table_number_force)
        return
    table.is_reserved = True
    table.user_name = faker.name()
    table.booking_time = "N/A"
    table.user_id = message.from_user.username
    await message.answer(f"Table {table.table_id} is booked")
    await state.clear()


@ds.message(Command("bookbynumber"))
async def book_by_number(message: types.Message, state: FSMContext):
    _logger.info("Start booking table by number")
    if await validate_chat_id(str(message.chat.id)):
        await message.answer("You are not allowed to use this command")
        return
    await message.answer("Please provide table number you want to book")
    await state.set_state(ManagerStates.waiting_for_table_number)


@ds.message(ManagerStates.waiting_for_table_number)
async def process_table_number(message: types.Message, state: FSMContext):
    _logger.info("Processing request for table number to book")
    table_number = message.text
    chosen_date = datetime.now()
    tables = tables_storage.get_tables_for_date(chosen_date.date())
    table = next((table for table in tables if table.table_id == int(table_number)), None)
    if table is None:
        await message.answer("Table with this number is not found")
        await state.set_state(ManagerStates.waiting_for_table_number)
        return
    if table.is_reserved:
        await message.answer("Table is already reserved")
        await state.set_state(ManagerStates.waiting_for_table_number)
        return
    await state.update_data({"table": table, "date": chosen_date})
    await message.answer("Please provide name you want to book the table for")
    await state.set_state(OrderStates.waiting_for_name)


async def main():
    try:
        if os.path.exists(backup_csv_file):
            tables_storage.upload_backup_file(backup_csv_file)
        await ds.start_polling(bot)
    except Exception as e:
        _logger.exception("Error while polling")
        tables_storage.backup_to_csv_file(backup_csv_file)
        raise e


if __name__ == "__main__":
    asyncio.run(main())
