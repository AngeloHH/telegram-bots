### What's this?
Central is an API that allows multiple bots to obtain and store information about users in an orderly way and avoiding duplicates of these. At first this started as a simple project to download "Anime" from AnimeFLV and learn how to use FastApi and deepen my knowledge of pyTelegramBotAPI but little by little the code became more complex.

#### Bot list:
**anime_bot:** Shows the list of daily anime chapters, animes in transmission and an anime search system. Shows detailed information (category, chapters and score) also allows a direct download from the server that hosts the selected chapter.

**manga_bot:** Say goodbye to the hassle of searching for the latest manga chapters and say hello to this bot! This is your one-stop destination for the latest manga chapters! This Telegram bot offers some commands for show a list of the most popular or trending daily chapters.

### How to install:

Installing packages:

    pip install -r requirements.txt

Executing central-api and bots:

    python3 central/main.py

    python3 anime_bot/main.py --token=<your-token>

    python3 manga_bot/main.py --token=<your-token>
