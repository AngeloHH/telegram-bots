import emoji


def get_stars(points=0.0): return ''.join(emoji.emojize(':star:') for _ in range(round(points)))


def chapter_list(chapters: list) -> str:
    text = 'Generando lista de capitulos diarios.\n'
    for index, chapter in enumerate(chapters):
        text += f"[{'%02d' % (index + 1)}] » "
        text += f"{chapter['title']} {chapter['chapter']}\n"
    return text


def anime_details(anime: dict) -> str:
    text = '📚 Título: {}\n📝 Sinopsis: {}\n🔖 Tipo: {}\n🌟 Puntos: {}'
    text = '[🆕 Nuevo] ' + text if 'is_new' in anime else text
    title, synopsis = anime['title'], anime['synopsis'][:350]
    stars = get_stars(anime['points'])
    return text.format(title, synopsis, anime['type'], stars)


def chapter_details(chapter: dict) -> str:
    index = chapter['title'].index('Episodio')
    title = chapter['title'][:index]
    text = '📚 Título: {}\n🎥 Episodio: {}'
    episode = chapter['title'].split(' ')[-1]
    return text.format(title, episode)
