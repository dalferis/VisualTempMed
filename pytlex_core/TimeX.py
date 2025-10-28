# Written by: jsegr004
# Last updated: jsegr004

from dataclasses import dataclass, field


@dataclass
class TimeX:
    tID: int
    value: str
    temporalFunction: bool
    phrase: str
    type: str = field(default='NONE')  # TimexType optional attribute
    mod: str = field(default='NONE')  # TimexMod optional attribute
    documentFunction: str = field(default='NONE')  # FunctionInDocument optional attribute
    anchorID: int = field(default=None)  # optional attribute
    quant: str = field(default=None)  # optional attribute
    freq: str = field(default=None)  # optional attribute
    beginPoint: int = field(default=None)
    endPoint: int = field(default=None)

    def __post_init__(self):
        if self.tID < 0:
            raise Exception("Error: Time id can't be less than zero.")

        accepted_types = {"DATE", "TIME", "DURATION", "SET", "NONE"}
        if self.type not in accepted_types:
            raise Exception("Error: Not acceptable TimeX Type - t" + str(self.tID))

        accepted_mods = {"BEFORE", "AFTER", "ON_OR_BEFORE", "ON_OR_AFTER", "LESS_THAN", "MORE_THAN", "EQUAL_OR_LESS",
                         "EQUAL_OR_MORE", "START", "MID", "END", "APPROX", "NONE"}
        if self.mod not in accepted_mods:
            raise Exception("Error: Not acceptable TimeX Mod - t" + str(self.tID))

        accepted_doc_functions = {"CREATION_TIME", "MODIFICATION_TIME", "PUBLICATION_TIME", "RELEASE_TIME",
                                  "RECEPTION_TIME", "EXPIRATION_TIME", "NONE"}
        if self.documentFunction not in accepted_doc_functions:
            raise Exception("Error: Not acceptable TimeX Document Function - t" + str(self.tID))

        if self.anchorID is not None:
            if self.anchorID < 0:
                raise Exception("Error: Anchor id can't be less than zero. - t" + str(self.tID))

        if self.beginPoint is not None:
            if self.beginPoint < 0:
                raise Exception("Error: beginPoint can't be less than zero. - t" + str(self.tID))

        if self.endPoint is not None:
            if self.endPoint < 0:
                raise Exception("Error: endPoint can't be less than zero. - t" + str(self.tID))

        # Is this a valid error? Example when type = 'SET' but quant and freq are none:
        #   in 'VOA19980303.1600.2745.tml' tID is 't120'
        # if self.type == 'SET' and (self.quant is None and self.freq is None):
        #     print("Error: quant or freq can't be None if type is SET - t" + str(self.tID))

    def get_id_str(self):
        return "t" + str(self.tID)

    def get_anchor_id_str(self):
        return "t" + str(self.anchorID)

    def get_begin_point_str(self):
        return "t" + str(self.beginPoint)

    def get_end_point_str(self):
        return "t" + str(self.endPoint)

    def __hash__(self):
        return hash(self.get_id_str())

    def to_json(self):
        t_type = self.type if self.type is not 'NONE' else "NULL"
        mod = self.mod if self.mod is not 'NONE' else "NULL"
        document_function = self.documentFunction if self.documentFunction is not 'NONE' else "NULL"
        anchor_id = self.get_anchor_id_str() if self.anchorID is not None else "NULL"
        quant = self.quant if self.quant is not None else "NULL"
        freq = self.freq if self.freq is not None else "NULL"
        begin_point = self.get_begin_point_str() if self.beginPoint is not None else "NULL"
        end_point = self.get_end_point_str() if self.endPoint is not None else "NULL"

        return f'{{"tID":"{self.get_id_str()}", "value":"{self.value}", "temporalFunction":"{self.temporalFunction}",' \
               f' "phrase":"{self.phrase}", "type":"{t_type}", "mod":"{mod}", "documentFunction":"' \
               f'{document_function}", "anchorID":"{anchor_id}", "quant":"{quant}", "freq":"{freq}", "beginPoint":"' \
               f'{begin_point}", "endPoint":"{end_point}"}}'
