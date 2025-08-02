import csv


def generate_tsv(schema, json_data, out_path):
    filters = Filter()
    selection = []
    for data in json_data:
        selection.extend(data.get(schema['selector'], []))            
    headers = schema['headers']
    rows = [headers]
    for item in selection:
        row = []
        for header in headers:
            filter_name = schema['filters'].get(header, None)
            raw_text = item.get(header, "")
            modified_text = filters.apply_filter(filter_name, raw_text)
            row.append(modified_text)
        rows.append(row)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerows(rows)


class Filter:
    @staticmethod
    def NOOP(text: str) -> str:
        return text

    @staticmethod
    def handshake_extend_href(text: str) -> str:
        result = "https://uoregon.joinhandshake.com" + text
        return result

    @staticmethod
    def handshake_extract_pay(text: str) -> str:
        tokens = text.split('\u00b7')
        filtered = list(filter(lambda t: "/" in t, tokens))
        if not filtered:
            return "N/A"
        return filtered[0].strip()

    @staticmethod
    def handshake_extract_type(text: str) -> str:
        tokens = text.split('\u00b7')
        check = ["Part-time", "Full-time", "Internship"]
        filtered = list(filter(lambda t: any(word in t for word in check), tokens))
        if not filtered:
            return "N/A"
        return filtered[0].strip()

    @staticmethod
    def handshake_extract_duration(text: str) -> str:
        tokens = text.split('\u00b7')
        filtered = list(filter(lambda t: "\u2014" in t, tokens))
        if not filtered:
            return "N/A"
        return filtered[0].strip()

    @staticmethod
    def handshake_extract_location(text: str) -> str:
        tokens = text.split('\u00b7')
        if not tokens:
            return "N/A"
        return tokens[0]

    @staticmethod
    def handshake_extract_deadline(text: str) -> str:
        tokens = text.split('\u00b7')
        if len(tokens) < 2:
            return "N/A"
        return tokens[1]

    def apply_filter(self, filter_name: str | None, text: str) -> str:
        if filter_name is None:
            return self.NOOP(text)
        filter_method = getattr(Filter, filter_name, None)
        if callable(filter_method):
            return filter_method(text)
        else:
            return self.NOOP(text)
