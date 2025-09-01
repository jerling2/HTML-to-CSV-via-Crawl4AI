class Transformer:
    
    def apply_transformation(self, function_name: str | None, text: str) -> str:
        if function_name is None:
            return self.NOOP(text)
        transformer_method = getattr(Transformer, function_name, None)
        if callable(transformer_method):
            return transformer_method(text)
        else:
            return self.NOOP(text)

    @staticmethod
    def NOOP(text: str) -> str:
        return text

    # --- User Defined Transformations --- # 

    @staticmethod
    def handshake_extract_job_id(text: str) -> str:
        result = text.split('/')[-1]
        return result

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
        return tokens[0].strip()

    @staticmethod
    def handshake_extract_deadline(text: str) -> str:
        tokens = text.split('\u00b7')
        if len(tokens) < 2:
            return "N/A"
        return tokens[1]

    @staticmethod
    def handshake_normalize_apply_type(text: str) -> str:
        return "internal" if text == "Apply" else "external"