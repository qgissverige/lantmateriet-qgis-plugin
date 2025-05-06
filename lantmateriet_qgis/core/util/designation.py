import re

from lantmateriet_qgis.core.util import cql2, municipalities

designation_re = re.compile(r"([^0-9]+) ?(?:([0-9]+|s|ga)(?::([0-9]+)?)?)?")


def parse_designation(designation: str) -> list[dict] | None:
    designation = designation_re.fullmatch(designation)
    if designation is None:
        return None
    designation_name = designation.group(1).strip()
    municipality = next(
        (
            k
            for k, v in municipalities.items()
            if designation_name.upper().startswith(v.upper())
        ),
        None,
    )
    filter_terms: list[dict] = []
    if municipality is not None:
        filter_terms.append(cql2.equals(cql2.property("kommunkod"), municipality))
        designation_name = designation_name[len(municipalities[municipality]) :].strip()
    filter_terms.append(
        cql2.startswith(cql2.property("trakt"), designation_name.upper())
    )
    if designation.group(2) is not None:
        if designation.group(3) is None:
            # the upstream API is _really_ slow when getting nested AND/OR queries, so we
            # have to split them up into two separate queries
            return [
                cql2.and_(
                    [
                        *filter_terms,
                        cql2.startswith(cql2.property("block"), designation.group(2)),
                    ]
                ),
                cql2.and_(
                    [
                        *filter_terms,
                        cql2.is_null(cql2.property("block")),
                        cql2.equals(cql2.property("enhet"), int(designation.group(2))),
                    ]
                ),
            ]
        else:
            filter_terms.append(
                cql2.equals(cql2.property("block"), int(designation.group(2)))
            )
            filter_terms.append(
                cql2.equals(cql2.property("enhet"), int(designation.group(3)))
            )
    return [cql2.and_(filter_terms)]


def parse_designation_exact(designation: str) -> dict | None:
    designation = designation_re.fullmatch(designation)
    if designation is None:
        return None
    designation_name = designation.group(1).strip()
    municipality = next(
        (
            k
            for k, v in municipalities.items()
            if designation_name.upper().startswith(v.upper())
        ),
        None,
    )
    filter_terms: list[dict] = []
    if municipality is not None:
        filter_terms.append(cql2.equals(cql2.property("kommunkod"), municipality))
        designation_name = designation_name[len(municipalities[municipality]) :].strip()
    filter_terms.append(cql2.equals(cql2.property("trakt"), designation_name.upper()))
    if designation.group(2) is None:
        return None
    if designation.group(3) is None:
        filter_terms.append(cql2.is_null(cql2.property("block")))
        filter_terms.append(
            cql2.equals(cql2.property("enhet"), int(designation.group(2)))
        )
    else:
        filter_terms.append(cql2.equals(cql2.property("block"), designation.group(2)))
        filter_terms.append(
            cql2.equals(cql2.property("enhet"), int(designation.group(3)))
        )
    return cql2.and_(filter_terms)
