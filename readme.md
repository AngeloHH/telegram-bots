### What's this?
Central is an API that allows multiple bots to obtain and store information about users in an orderly way and avoiding duplicates of these. At first this started as a simple project to download "Anime" from AnimeFLV and learn how to use FastApi and deepen my knowledge of pyTelegramBotAPI but little by little the code became more complex.

#### Bot list:
**anime_bot:** Shows the list of daily anime chapters, animes in transmission and an anime search system. Shows detailed information (category, chapters and score) also allows a direct download from the server that hosts the selected chapter.

**manga_bot:** List the most popular or trending daily chapters using telegraph.

### How to install:

Installing packages:

    pip install -r requirements.txt

Executing central-api and bots:

    python3 central/main.py

    python3 anime_bot/main.py

    python3 manga_bot/main.py
