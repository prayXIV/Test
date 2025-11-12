# RSS Feed Generator

Автоматическая генерация RSS-фидов для блогов и сайтов, которые не предоставляют собственные RSS-фиды.

## Описание

Этот проект создает RSS-фиды для следующих источников:

- **DeepMind Blog** - https://deepmind.google/blog/
- **DeepMind Publications** - https://deepmind.google/research/publications/
- **arXiv cs.AI** - https://arxiv.org/list/cs.AI/recent

## Структура проекта

```
.
├── feed_generators/          # Генераторы RSS-фидов
│   ├── deepmind_blog.py
│   ├── deepmind_publications.py
│   ├── arxiv_cs_ai.py
│   └── date_utils.py        # Утилиты для парсинга дат
├── run_all_feeds.py          # Скрипт для запуска всех генераторов
├── requirements.txt          # Зависимости Python
├── .github/workflows/        # GitHub Actions
│   └── generate_feeds.yml
└── feed_*.xml               # Сгенерированные RSS-фиды
```

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd rss-feeds
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Использование

### Запуск всех генераторов

```bash
python run_all_feeds.py
```

### Запуск отдельного генератора

```bash
python feed_generators/deepmind_blog.py
python feed_generators/deepmind_publications.py
python feed_generators/arxiv_cs_ai.py
```

## Автоматическое обновление

GitHub Action настроен на автоматический запуск каждый час. Фиды обновляются автоматически и коммитятся в репозиторий.

## Генерируемые фиды

После запуска генераторов создаются следующие файлы:

- `feed_deepmind_blog.xml`
- `feed_deepmind_publications.xml`
- `feed_arxiv_cs_ai.xml`

## Добавление нового генератора

1. Создайте новый Python файл в директории `feed_generators/`
2. Реализуйте функцию `generate_feed()` которая:
   - Загружает HTML страницу
   - Парсит контент с помощью BeautifulSoup
   - Создает RSS фид с помощью FeedGenerator
   - Сохраняет фид в файл `feed_<name>.xml`

Пример структуры:

```python
#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime

def generate_feed():
    url = "https://example.com/blog"
    # ... парсинг и генерация фида ...
    fg.rss_file('feed_example.xml')

if __name__ == "__main__":
    generate_feed()
```

## Зависимости

- `requests` - для HTTP запросов
- `beautifulsoup4` - для парсинга HTML
- `lxml` - парсер для BeautifulSoup
- `feedgen` - для генерации RSS фидов

## Лицензия

MIT

