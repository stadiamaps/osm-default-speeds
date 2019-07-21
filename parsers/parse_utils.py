from bs4 import element
from lark import Lark

from parsers import SPEED_GRAMMAR

parser = Lark(SPEED_GRAMMAR)


class ParseError(Exception):
    pass


class TableRowHelper:
    """A simplified interface around a set of table rows from bs4.

    This abstracts all the evil stuff like rowspan and colspan so that the data
    can be reasonably parsed.
    """

    def __init__(self):
        self.td_cache = {}

    def set_tds(self, tds: [element.Tag]):
        # Nuke any existing cache entries that "expire" this round (rowspan)
        for k in list(self.td_cache.keys()):
            (remaining, value) = self.td_cache[k]
            if remaining == 1:
                del self.td_cache[k]
            else:
                self.td_cache[k] = (remaining - 1, value)

        # Add new data for this row
        col_idx = 0
        for td in tds:
            rowspan = int(td.get("rowspan", 1))

            while col_idx in self.td_cache:
                col_idx += 1  # Skip cols that are around from a prev iteration due to rowspan

            for _ in range(int(td.get("colspan", 1))):
                self.td_cache[col_idx] = (rowspan, td)
                col_idx += 1

    def get_td(self, idx) -> element.Tag:
        return self.td_cache[idx][1]


def is_uninteresting(tag: element.Tag):
    return tag.name in {"sup", "img"}


def parse_speed_table(table, speed_parse_func) -> dict:
    column_names = []
    result = {}
    table_row_helper = TableRowHelper()

    # Remove links (footnotes etc), images, etc. that don't serialize well.
    for junk_tag in table.find_all(is_uninteresting):
        junk_tag.decompose()

    for row in table.find_all("tr"):
        # Handle column names
        th_tags = row.find_all("th")
        if len(th_tags) > 0:
            if len(column_names) == 0:
                for th in th_tags:
                    th_text = th.get_text(strip=True)
                    for _ in range(int(th.get("colspan", 1))):
                        column_names.append(th_text)
            else:
                for (i, th) in enumerate(th_tags):
                    th_text = th.get_text(strip=True)
                    if th_text:
                        for j in range(int(th.get("colspan", 1))):
                            column_names[i + j] = th_text

        # Loop through columns
        tds = row.find_all("td")
        table_row_helper.set_tds(tds)
        if tds:
            country_code = table_row_helper.get_td(0).get_text(strip=True)
            road_type = table_row_helper.get_td(1).get_text(strip=True) or "(default)"

            speeds_by_vehicle_type = {}
            for col_idx in range(2, len(column_names)):
                td = table_row_helper.get_td(col_idx)
                speeds = td.get_text(strip=True)

                if speeds:
                    vehicle_type = column_names[col_idx]
                    try:
                        parsed_speeds = speed_parse_func(speeds)
                    except ParseError as e:
                        raise ParseError(f'Parsing "{vehicle_type}" for "{road_type}" in {country_code}:\n{str(e)}')

                    speeds_by_vehicle_type[vehicle_type] = parsed_speeds

            if country_code in result:
                result[country_code][road_type] = speeds_by_vehicle_type
            else:
                result[country_code] = {road_type: speeds_by_vehicle_type}

    return result