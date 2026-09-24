"""Write the synthetic publications as OAI-PMH responses, the format the ZORA collector reads.

    ListSets.xml       the faculty > institute > division structure (verb=ListSets)
    ListRecords.xml    the first page of records (verb=ListRecords, metadataPrefix=oai_dc)
    page-0002.xml ...  the following pages, linked with <resumptionToken>

`pipeline/zora/collector.py --from-dir <folder>` reads these files instead of calling ZORA.
"""

from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

from .organizations import DIVISIONS

HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
  <responseDate>{today}T00:00:00Z</responseDate>
  <request verb="{verb}">https://dummy.example.org/oai</request>
"""
FOOTER = "</OAI-PMH>\n"


def _element(name: str, value: str, indent: str) -> str:
    return f"{indent}<{name}>{escape(value)}</{name}>\n"


def write_list_sets(folder: Path) -> None:
    sets = {}
    for d in DIVISIONS:
        sets[d.faculty.set_spec] = d.faculty.name
        sets[f"{d.faculty.set_spec}:{d.institute.set_spec}"] = f"{d.faculty.name}:{d.institute.name}"
        sets[d.set_spec] = f"{d.faculty.name}:{d.institute.name}:{d.division.name}"

    body = "".join(
        f"    <set>\n{_element('setSpec', spec, '      ')}{_element('setName', name, '      ')}    </set>\n"
        for spec, name in sets.items()
    )
    xml = HEADER.format(today=date.today(), verb="ListSets") + f"  <ListSets>\n{body}  </ListSets>\n" + FOOTER
    (folder / "ListSets.xml").write_text(xml, encoding="utf-8")


def _record(publication: dict) -> str:
    i = "          "
    creators = "".join(_element("dc:creator", author, i) for author in publication["authors"])
    return (
        "    <record>\n"
        "      <header>\n"
        f"{_element('identifier', publication['oai_identifier'], '        ')}"
        f"{_element('datestamp', publication['date'], '        ')}"
        f"{_element('setSpec', publication['set_spec'], '        ')}"
        "      </header>\n"
        "      <metadata>\n"
        '        <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"'
        ' xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        f"{_element('dc:title', publication['title'], i)}"
        f"{creators}"
        f"{_element('dc:description', publication['description'], i)}"
        f"{_element('dc:publisher', publication['publisher'], i)}"
        f"{_element('dc:date', publication['date'], i)}"
        f"{_element('dc:type', 'Journal Article, refereed, original work', i)}"
        f"{_element('dc:source', publication['source'], i)}"
        f"{_element('dc:language', publication['language'], i)}"
        f"{_element('dc:format', publication['format'], i)}"
        "        </oai_dc:dc>\n"
        "      </metadata>\n"
        "    </record>\n"
    )


def write_list_records(folder: Path, publications: list[dict], page_size: int) -> int:
    pages = [publications[i:i + page_size] for i in range(0, len(publications), page_size)]
    for number, page in enumerate(pages, start=1):
        filename = "ListRecords.xml" if number == 1 else f"page-{number:04d}.xml"
        next_token = f"page-{number + 1:04d}" if number < len(pages) else ""
        token = (
            f'    <resumptionToken completeListSize="{len(publications)}" cursor="{(number - 1) * page_size}">'
            f"{next_token}</resumptionToken>\n"
        )
        xml = (
            HEADER.format(today=date.today(), verb="ListRecords")
            + "  <ListRecords>\n"
            + "".join(_record(p) for p in page)
            + token
            + "  </ListRecords>\n"
            + FOOTER
        )
        (folder / filename).write_text(xml, encoding="utf-8")
    return len(pages)
