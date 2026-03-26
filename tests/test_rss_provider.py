from app.providers.rss_provider import RSSProvider


def test_rss_provider_loads_items() -> None:
    provider = RSSProvider()
    items = provider.load_all()
    assert items
    assert items[0].title
