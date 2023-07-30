def comic_detail(comic: dict, max_len: int) -> str:
    text = '📚 Título: {}\n🔖 Géneros: {}\n📝 Sinopsis: {}\n🏷 Capítulos: {}'
    genres = ', '.join(comic['genres'])
    chapters, synopsis = len(comic['chapters']), comic['synopsis']
    synopsis = synopsis[:max_len].strip()
    synopsis += '' if len(comic['synopsis']) < max_len else '...'
    return text.format(comic['title'], genres, synopsis, chapters)


def comic_model(comic: dict) -> str:
    text = '📚 Título: {}\n🌟 Puntuación: {}\n📖 Tipo: {}\n📖 Demografía: {}'
    book_type, demography = comic['book-type'], comic['demography']
    return text.format(comic['title'], comic['score'], book_type, demography)


def end_task() -> str:
    return ''
