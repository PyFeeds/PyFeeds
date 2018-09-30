from feeds.loaders import FeedItemLoader


def generate_feed_header(
    title=None,
    subtitle=None,
    link=None,
    path=None,
    author_name=None,
    icon=None,
    logo=None,
):
    il = FeedItemLoader()
    il.add_value("title", title)
    il.add_value("subtitle", subtitle)
    il.add_value("link", link)
    il.add_value("path", path)
    il.add_value("author_name", author_name)
    il.add_value("icon", icon)
    il.add_value("logo", logo)
    return il.load_item()
