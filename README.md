## Description

#### Telegram bot to book tables in the restaurant. It allows to store, cancel, check bookings for tables in different dates
#### There to use it you need to have telegram account and set up chat with managers, where bot will send all booking details and allows to manage bookings on management level


## Installation
### 1. Setup environment

#### Getting Your Telegram Bot Token from BotFather
To set up and authenticate your bot, you’ll need a unique token ID from Telegram’s BotFather. Follow these steps:

1. Open Telegram and search for the user BotFather. BotFather is the official bot that manages all Telegram bots.

2. Start a Chat with BotFather by selecting it and clicking the Start button. You can also send /start to initiate a conversation.

3. Create a New Bot by sending the command `/newbot`. BotFather will prompt you to:

   - Choose a Name: Enter a name for your bot (e.g., MyOrderBot).
   - Choose a Username: Enter a unique username that ends with bot (e.g., MyOrderBot_bot).

4. Receive Your Token: Once the bot is created, BotFather will provide you with a message that includes your bot’s unique token ID:

`Use this token to access the HTTP API:
123456789:ABCdefGhIJKlmNOPQRstUVWXyz0123456789`

- Copy this token and keep it secure. This token allows you to authenticate your bot with Telegram’s API.
Add the Token to Your Code: In your project, set the token as an environment variable or insert it directly where required in your code. Example:

`api_token = "123456789:ABCdefGhIJKlmNOPQRstUVWXyz0123456789"`

6. Manage Your Bot: You can use additional commands with BotFather, like `/setdescription` to add a description or `/setuserpic` to add a profile picture for your bot.

#### Setting Up Your Environment
Using docker image:
1. Clone the repository to your local machine.
2. Create a .env file in the project directory and add the following environment variables
   - TELEGRAM_API_TOKEN - token you got from @botfather
   - GROUP_CHAT_ID - chat id of the group where bot will send booking details and manage bookings
   - TABLES_FILE - path to the file where table's distribution is defined (.csv file with columns table_number, capacity)
3. Build a docker image with the following command: `docker build -t booking_bot .`
4. Run the docker container with the following command: `docker run -d booking_bot --env-file .env`

Using python:
1. Clone the repository to your local machine:
2. Create a .env file in the project directory and add the following environment variables
   - TELEGRAM_API_TOKEN - token you got from @botfather
   - GROUP_CHAT_ID - chat id of the group where bot will send booking details and manage bookings
   - TABLES_FILE - path to the file where table's distribution is defined (.csv file with columns table_number, capacity)
3. Install the required packages with the following command: `pip install -r requirements.txt`
4. Run the bot with the following command: `python run_bot.py`

### 2. Usage

User Booking Process:

The user sends /book, and the bot will prompt for details like date, table size, and time.
After the booking is confirmed, the user receives a summary and confirmation message.

User can call /cancelbooking and specify the booking id to cancel the booking.

Manager Commands:

A manager in the designated group can use /checkbookings and specify a date to view reserved tables.
The manager can also use /cancelbooking and specify the booking id to cancel the booking and book table themselves.
