# Generate a spider documentation template.

import click


def render_template(spider_name):
    conf = "Configuration"

    lines = [".. _spider_{}:".format(spider_name)]
    lines.append("")
    lines.append(spider_name)
    lines.append("-" * len(spider_name))
    lines.append(
        "TODO: A summary about this spider with a link to the "
        "`website <https://{}>`_.".format(spider_name)
    )
    lines.append("")
    lines.append(conf)
    lines.append("~" * len(conf))
    lines.append("Add ``{}`` to the list of spiders:".format(spider_name))
    lines.append("")
    lines.append(".. code-block:: ini")
    lines.append("")
    lines.append("   # List of spiders to run by default, one per line.")
    lines.append("   spiders =")
    lines.append("     {}".format(spider_name))
    lines.append("")
    return "\n".join(lines)


@click.command()
@click.argument("spider_name")
def main(spider_name):
    print(render_template(spider_name))


if __name__ == "__main__":
    main()
