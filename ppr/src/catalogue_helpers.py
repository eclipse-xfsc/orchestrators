"""Provide helpers for Self-Description catalogues."""

import hashlib
import json
from enum import Enum
from pathlib import Path
from typing import Dict, Any
from typing import List, Optional
from uuid import uuid4


class IaCType(Enum):
    """Enum that can distinct between different types of IaC (deployment instructions)."""

    TOSCA = "tosca"
    TERRAFORM = "terraform"


class InfrastructureAsCode:
    """Entity for Infrastructure as Code (IaC) within Self-Description."""

    def __init__(self, typ: IaCType, url: str, inputs: Optional[str] = None) -> None:
        """
        Initialize SelfDescription object.

        :param typ: IaCType object
        :param url: IaC URL
        :param inputs: IaC inputs (optional)
        """
        self.typ = typ
        self.url = url
        self.inputs = inputs

    def to_json(self) -> Dict[str, Any]:
        """
        Dump InfrastructureAsCode object to JSON.

        :return: JSON for InfrastructureAsCode object
        """
        iac = {
            "type": self.typ.value,
            "url": self.url
        }

        if self.inputs:
            iac["inputs"] = self.inputs

        return iac


class SelfDescription:
    """Entity for Self-Description."""

    def __init__(self, name: str, json_ld: Dict[str, Any], sha256: Optional[str] = None) -> None:
        """
        Initialize SelfDescription object.

        :param name: Self-Description name
        :param json_ld: Self Description JSON-LD object
        """
        self.name = name
        self.json_ld = json_ld
        self.sha256 = sha256 if sha256 is not None else hashlib.sha256(name.encode("utf-8")).hexdigest()
        self.description = ""
        self.iac: List[InfrastructureAsCode] = []

        # TODO: update this when we know how Self-Description should be described
        if "dct:description" in json_ld:
            self.description = json_ld["dct:description"].get("@value", "")

        # TODO: update this when we know how Self-Description specifies IaC
        if "gax-service:infrastructureAsCode" in json_ld:
            iac_json_ld = json_ld["gax-service:infrastructureAsCode"]
            if isinstance(iac_json_ld, list):
                self._transform_iac(json_ld["gax-service:infrastructureAsCode"])

    def _transform_iac(self, json_ld_iac: List[Dict[str, Any]]) -> None:
        """
        Retrieve and transform IaC (URL and inputs) that implements the Self-Description.

        :return: IaC as a list of dicts
        """
        for iac_entry in json_ld_iac:
            iac_entry_type = iac_entry.get("@type", None)

            if iac_entry_type:
                iac_type = None
                iac_url = None
                iac_inputs = None

                for typ in IaCType:
                    if typ.value == iac_entry_type.replace("iac:", ""):
                        iac_type = typ
                        break

                iac_entry_url = iac_entry.get("iac:url", None)
                if iac_entry_url:
                    iac_url = iac_entry_url.get("@value", None)

                iac_entry_inputs = iac_entry.get("iac:inputs", None)
                if iac_entry_inputs:
                    iac_inputs = iac_entry_inputs.get("@value", None)

                if iac_type and iac_url:
                    self.iac.append(InfrastructureAsCode(iac_type, iac_url, iac_inputs))

    def filter_iac(self, iac_type: Optional[IaCType]) -> List[InfrastructureAsCode]:
        """
        Filter IaC (URL and inputs) that implements the Self-Description.

        :param iac_type: IaCType object or None
        :return: IaC as a list of dicts
        """
        filtered_iac = []
        if self.iac and iac_type:
            for iac in self.iac:
                if iac.typ.value == iac_type.value:
                    filtered_iac.append(iac)
                    break

        return filtered_iac if filtered_iac else self.iac

    def to_json(self) -> Dict[str, Any]:
        """
        Dump SelfDescription object to JSON.

        :return: JSON for SelfDescription object
        """
        return {
            "sha256": self.sha256,
            "name": self.name,
            "description": self.description,
            "iac": [iac.to_json() for iac in self.iac]
        }


class SelfDescriptionCatalogue:
    """Entity for catalogue of Self-Descriptions."""

    def __init__(self, name: str, description: str = "", uuid: Optional[str] = None) -> None:
        """
        Initialize SelfDescriptionCatalogue object.

        :param name: Catalogue name
        :param description: Catalogue description
        """
        self.name = name
        self.description = description
        self.uuid = uuid if uuid is not None else str(uuid4().hex)
        self.self_descriptions: List[SelfDescription] = []

    def add_self_description(self, self_description: SelfDescription) -> None:
        """
        Add new Self-Description to the catalogue.

        :param self_description: Description object
        """
        self.self_descriptions.append(self_description)

    def remove_self_description_by_sha256(self, sha256: str) -> None:
        """
        Remove Self-Description from the catalogue.

        :param sha256: SHA-256 hash of the Self-Description
        """
        self.self_descriptions = list(filter(lambda sd: sd.sha256 != sha256, self.self_descriptions))

    def get_self_descriptions_by_sha256(self, sha256: str) -> List[SelfDescription]:
        """
        Get Self-Descriptions from the catalogue by its SHA-256 hash.

        :param sha256: SHA-256 hash of the Self-Description
        :return: List of SelfDescription objects
        """
        return list(filter(lambda sd: sd.sha256.lower() == sha256.lower(), self.self_descriptions))

    def get_self_descriptions_by_keyword(self, keyword: str) -> List[SelfDescription]:
        """
        Get Self-Descriptions from the catalogue by keyword.

        :param keyword: Keyword to be searched for within Self-Description name and description
        :return: List of SelfDescription objects
        """
        return list(filter(lambda sd: keyword.lower() in sd.name.lower() or keyword.lower() in sd.description.lower(),
                           self.self_descriptions))

    def to_json(self) -> Dict[str, Any]:
        """
        Dump SelfDescriptionCatalogue object to JSON.

        :return: JSON for SelfDescriptionCatalogue object
        """
        return {
            "uuid": self.uuid,
            "name": self.name,
            "description": self.description
        }


# TODO: remove this mock function of example catalogue when PPR is really connected to the Self-Description catalogues
def self_description_catalogue_mock(directory: Path, name: str, description: str) -> SelfDescriptionCatalogue:
    """
    Mock the Self-Description example catalogue.

    :param directory: Folder with Self-Descriptions as JSON-LD files
    :param name: Catalogue name
    :param description: Catalogue description
    :return: SelfDescriptionCatalogue object containing mocked catalogue
    """
    mocked_self_description_catalogue = SelfDescriptionCatalogue(name, description)
    for path in directory.rglob("*.json"):
        with path.open("r") as json_ld_file:
            try:
                json_ld = json.load(json_ld_file)
                self_description = SelfDescription(path.stem, json_ld)
                mocked_self_description_catalogue.add_self_description(self_description)
            except json.JSONDecodeError:
                continue

    return mocked_self_description_catalogue
